#!/usr/bin/env python3
"""更新 jfkf Repo 索引：添加新 deb 包，重新生成 Packages/Packages.gz/Release"""
import subprocess, os, hashlib, tarfile, io, gzip, time

REPO = "/var/minis/workspace/repo"
NEW_DEBS = [
    "com.hx.120_2.2_iphoneos-arm64e.deb",
    "com.hx.120_2.3_iphoneos-arm64e.deb",
]

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def sha(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def extract_control(deb_path):
    """从 deb 提取 control 文件内容"""
    # ar x 提取 control.tar.gz
    tmpdir = f"/tmp/deb_extract_{os.getpid()}"
    os.makedirs(tmpdir, exist_ok=True)
    run(["ar", "x", deb_path, "control.tar.gz"], cwd=tmpdir)
    ctl_gz = os.path.join(tmpdir, "control.tar.gz")
    with tarfile.open(ctl_gz, 'r:gz') as tar:
        try:
            data = tar.extractfile("./control").read().decode()
        except:
            # 尝试不带 ./
            data = tar.extractfile("control").read().decode()
    import shutil
    shutil.rmtree(tmpdir)
    # 解析 control 字段
    fields = {}
    for line in data.strip().split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            fields[k.strip()] = v.strip()
    return fields

def gen_entry(deb_name, fields, path):
    size = os.path.getsize(path)
    md5 = sha(path, 'md5')
    s1 = sha(path, 'sha1')
    s256 = sha(path, 'sha256')
    return f"""Package: {fields.get('Package','')}
Name: {fields.get('Name','')}
Depends: {fields.get('Depends','')}
Description: {fields.get('Description','')}
Maintainer: {fields.get('Maintainer','')}
Author: {fields.get('Author','')}
Section: {fields.get('Section','')}
Architecture: {fields.get('Architecture','')}
Version: {fields.get('Version','')}
Installed-Size: {fields.get('Installed-Size','')}
Filename: ./{deb_name}
Size: {size}
MD5sum: {md5}
SHA1: {s1}
SHA256: {s256}

"""

# 1. 读取现有 Packages
with open(os.path.join(REPO, "Packages"), 'r') as f:
    existing = f.read().rstrip('\n')

# 2. 生成新条目
new_entries = ""
for deb in NEW_DEBS:
    path = os.path.join(REPO, deb)
    fields = extract_control(path)
    entry = gen_entry(deb, fields, path)
    new_entries += entry
    print(f"✅ {deb} → {fields.get('Package')} v{fields.get('Version')}")

# 3. 合并 Packages
packages = existing + "\n\n" + new_entries
with open(os.path.join(REPO, "Packages"), 'w') as f:
    f.write(packages)

# 4. 生成 Packages.gz
with open(os.path.join(REPO, "Packages"), 'rb') as f_in:
    with gzip.open(os.path.join(REPO, "Packages.gz"), 'wb') as f_out:
        f_out.write(f_in.read())

# 5. 更新 Release
def file_hashes(path):
    size = os.path.getsize(path)
    return {
        'size': size,
        'md5': sha(path, 'md5'),
        'sha1': sha(path, 'sha1'),
        'sha256': sha(path, 'sha256'),
    }

pkg_h = file_hashes(os.path.join(REPO, "Packages"))
gz_h = file_hashes(os.path.join(REPO, "Packages.gz"))
date_str = time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime())

release = f"""Origin: jfkf Repo
Label: jfkf Repo
Suite: stable
Version: 1.0
Codename: jfkf
Architectures: iphoneos-arm64 iphoneos-arm64e
Components: main
Description: jfkf personal jailbreak repo (roothide, iOS 15.4)
Date: {date_str}
MD5Sum:
 {pkg_h['md5']}             {pkg_h['size']} Packages
 {gz_h['md5']}              {gz_h['size']} Packages.gz
SHA1:
 {pkg_h['sha1']}             {pkg_h['size']} Packages
 {gz_h['sha1']}              {gz_h['size']} Packages.gz
SHA256:
 {pkg_h['sha256']}             {pkg_h['size']} Packages
 {gz_h['sha256']}              {gz_h['size']} Packages.gz
"""

with open(os.path.join(REPO, "Release"), 'w') as f:
    f.write(release)

print(f"\n=== 索引更新完成 ===")
print(f"Packages: {pkg_h['size']} bytes")
print(f"Packages.gz: {gz_h['size']} bytes")
print(f"Date: {date_str}")
print("\n=== 完整 Packages ===")
print(packages)
print("\n=== Release ===")
print(release)
