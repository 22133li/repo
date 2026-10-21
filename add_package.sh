#!/bin/bash
# 生成 Packages 条目并更新 Release 文件
set -e
cd /var/minis/workspace/repo

# ---- 1. 为两个新包生成 Packages 条目 ----
gen_entry() {
    local deb="$1"
    local size=$(stat -c %s "$deb")
    local md5=$(md5sum "$deb" | cut -d' ' -f1)
    local sha1=$(sha1sum "$deb" | cut -d' ' -f1)
    local sha256=$(sha256sum "$deb" | cut -d' ' -f1)
    
    # 从 control 提取字段
    local ctrl=$(ar x "$deb" control.tar.gz && tar xzOf control.tar.gz ./control && rm -f control.tar.gz)
    
    echo "Package: $(echo "$ctrl" | grep '^Package:' | cut -d' ' -f2-)"
    echo "Name: $(echo "$ctrl" | grep '^Name:' | cut -d' ' -f2-)"
    echo "Depends: $(echo "$ctrl" | grep '^Depends:' | cut -d' ' -f2-)"
    echo "Description: $(echo "$ctrl" | grep '^Description:' | cut -d' ' -f2-)"
    echo "Maintainer: $(echo "$ctrl" | grep '^Maintainer:' | cut -d' ' -f2-)"
    echo "Author: $(echo "$ctrl" | grep '^Author:' | cut -d' ' -f2-)"
    echo "Section: $(echo "$ctrl" | grep '^Section:' | cut -d' ' -f2-)"
    echo "Architecture: $(echo "$ctrl" | grep '^Architecture:' | cut -d' ' -f2-)"
    echo "Version: $(echo "$ctrl" | grep '^Version:' | cut -d' ' -f2-)"
    echo "Installed-Size: $(echo "$ctrl" | grep '^Installed-Size:' | cut -d' ' -f2-)"
    echo "Filename: ./$deb"
    echo "Size: $size"
    echo "MD5sum: $md5"
    echo "SHA1: $sha1"
    echo "SHA256: $sha256"
    echo ""
}

# 生成两个新条目
gen_entry "com.hx.120_2.2_iphoneos-arm64e.deb"
gen_entry "com.hx.120_2.3_iphoneos-arm64e.deb"

# ---- 2. 追加到现有 Packages 文件 ----
# 先读取现有 Packages 内容
EXISTING=$(cat Packages)
# 生成新条目
NEW_ENTRIES=$(gen_entry "com.hx.120_2.2_iphoneos-arm64e.deb"; gen_entry "com.hx.120_2.3_iphoneos-arm64e.deb")
# 合并
echo "$EXISTING" > Packages.new
echo "$NEW_ENTRIES" >> Packages.new
mv Packages.new Packages

# ---- 3. 生成 Packages.gz ----
gzip -c Packages > Packages.gz

# ---- 4. 更新 Release 文件 ----
PKG_SIZE=$(stat -c %s Packages)
GZ_SIZE=$(stat -c %s Packages.gz)
PKG_MD5=$(md5sum Packages | cut -d' ' -f1)
GZ_MD5=$(md5sum Packages.gz | cut -d' ' -f1)
PKG_SHA1=$(sha1sum Packages | cut -d' ' -f1)
GZ_SHA1=$(sha1sum Packages.gz | cut -d' ' -f1)
PKG_SHA256=$(sha256sum Packages | cut -d' ' -f1)
GZ_SHA256=$(sha256sum Packages.gz | cut -d' ' -f1)
DATE=$(date -u +"%a, %d %b %Y %H:%M:%S UTC")

cat > Release << EOF
Origin: jfkf Repo
Label: jfkf Repo
Suite: stable
Version: 1.0
Codename: jfkf
Architectures: iphoneos-arm64 iphoneos-arm64e
Components: main
Description: jfkf personal jailbreak repo (roothide, iOS 15.4)
Date: $DATE
MD5Sum:
 $PKG_MD5             $PKG_SIZE Packages
 $GZ_MD5              $GZ_SIZE Packages.gz
SHA1:
 $PKG_SHA1             $PKG_SIZE Packages
 $GZ_SHA1              $GZ_SIZE Packages.gz
SHA256:
 $PKG_SHA256             $PKG_SIZE Packages
 $GZ_SHA256              $GZ_SIZE Packages.gz
EOF

echo "=== 索引更新完成 ==="
echo "Packages 大小: $PKG_SIZE bytes"
echo "Packages.gz 大小: $GZ_SIZE bytes"
echo ""
echo "=== 完整 Packages 内容 ==="
cat Packages
echo ""
echo "=== Release 文件 ==="
cat Release
