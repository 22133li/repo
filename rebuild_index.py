#!/usr/bin/env python3
"""扫描仓库所有 deb，重新生成完整 Packages/Packages.gz/Release"""
import subprocess, os, hashlib, gzip, time, tarfile, io, shutil, tempfile

REPO = "/var/minis/workspace/repo"

def sha(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def extract_control(deb_path):
    """从 deb 提取 control 字段，自动检测 gz/xz"""
    tmp = tempfile.mkdtemp()
    # ar 提取 control.tar.*
    subprocess.run(["ar", "x", deb_path], cwd=tmp, capture_output=True)
    ctl = None
    for name in ["control.tar.gz", "control.tar.xz", "control.tar"]:
        p = os.path.join(tmp, name)
        if os.path.exists(p):
            ctl = p
            mode = "r:gz" if name.endswith(".gz") else ("r:xz" if name.endswith(".xz") else "r:")
            break
    if not ctl:
        shutil.rmtree(tmp)
        raise RuntimeError(f"No control archive in {deb_path}")
    with tarfile.open(ctl, mode) as tar:
        for member in ["./control", "control"]:
            try:
                data = tar.extractfile(member).read().decode()
                break
            except:
                continue
    shutil.rmtree(tmp)
    fields = {}
    for line in data.strip().split('\n'):
        if ':' in line and not line.startswith(' '):
            k, v = line.split(':', 1)
            fields[k.strip()] = v.strip()
    return fields

def gen_entry(deb_name, path):
    f = extract_control(path)
    size = os.path.getsize(path)
    # 按字段顺序生成，缺失的字段跳过
    lines = []
    order = ["Package","Name","Source","Depends","Conflicts","Replaces","Provides",
             "Description","Maintainer","Author","Section","Priority",
             "Architecture","Version","Installed-Size"]
    for key in order:
        if key in f:
            lines.append(f"{key}: {f[key]}")
    lines.append(f"Filename: ./{deb_name}")
    lines.append(f"Size: {size}")
    lines.append(f"MD5sum: {sha(path,'md5')}")
    lines.append(f"SHA1: {sha(path,'sha1')}")
    lines.append(f"SHA256: {sha(path,'sha256')}")
    return '\n'.join(lines) + '\n\n'

# 1. 扫描所有 deb 文件
debs = sorted([f for f in os.listdir(REPO) if f.endswith('.deb')])
print(f"找到 {len(debs)} 个 deb 文件")

# 2. 生成完整 Packages
packages = ""
for deb in debs:
    path = os.path.join(REPO, deb)
    entry = gen_entry(deb, path)
    packages += entry
    f = extract_control(path)
    print(f"  ✅ {deb} → {f.get('Package','?')} v{f.get('Version','?')} ({f.get('Architecture','?')})")

with open(os.path.join(REPO, "Packages"), 'w') as fh:
    fh.write(packages)

# 3. Packages.gz
with open(os.path.join(REPO, "Packages"), 'rb') as fin:
    with gzip.open(os.path.join(REPO, "Packages.gz"), 'wb') as fout:
        fout.write(fin.read())

# 4. Release
def fh(p):
    s = os.path.getsize(p)
    return {'size': s, 'md5': sha(p,'md5'), 'sha1': sha(p,'sha1'), 'sha256': sha(p,'sha256')}
p = fh(os.path.join(REPO,"Packages"))
g = fh(os.path.join(REPO,"Packages.gz"))
d = time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime())
release = f"""Origin:  往右自用源
Label:  往右自用源
Suite: stable
Version: 1.0
Codename: jfkf
Architectures: iphoneos-arm64 iphoneos-arm64e
Components: main
Description:  往右自用源
Date: {d}
MD5Sum:
 {p['md5']}             {p['size']} Packages
 {g['md5']}              {g['size']} Packages.gz
SHA1:
 {p['sha1']}             {p['size']} Packages
 {g['sha1']}              {g['size']} Packages.gz
SHA256:
 {p['sha256']}             {p['size']} Packages
 {g['sha256']}              {g['size']} Packages.gz
"""
with open(os.path.join(REPO,"Release"),'w') as fh2:
    fh2.write(release)

print(f"\n=== 索引重建完成 ===")
print(f"Packages: {p['size']} bytes | Packages.gz: {g['size']} bytes")
print(f"Date: {d}")
