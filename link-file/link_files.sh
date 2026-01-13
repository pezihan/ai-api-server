#!/bin/bash

# 脚本功能：将源目录下所有文件（含隐藏文件）软链接到目标目录
# 使用方法：bash link_files.sh 源目录绝对路径 目标目录绝对路径

# 1. 检查参数数量是否为2个
if [ $# -ne 2 ]; then
    echo "❌ 错误：参数数量不正确！"
    echo "✅ 正确用法：$0 <源目录绝对路径> <目标目录绝对路径>"
    echo "🔍 示例：$0 /home/user/a /home/user/b"
    exit 1
fi

# 2. 接收命令行参数
A_DIR="$1"  # 第一个参数：源目录（要被映射的目录）
B_DIR="$2"  # 第二个参数：目标目录（映射到的目录）

# 3. 检查源目录是否存在且是目录
if [ ! -d "$A_DIR" ]; then
    echo "❌ 错误：源目录 '$A_DIR' 不存在或不是有效目录！"
    exit 1
fi

# 4. 确保目标目录存在（不存在则创建）
mkdir -p "$B_DIR"
if [ ! -d "$B_DIR" ]; then
    echo "❌ 错误：目标目录 '$B_DIR' 创建失败！"
    exit 1
fi

# 5. 循环创建软链接（含隐藏文件，跳过空匹配）
echo "🔄 开始创建软链接，源目录：$A_DIR → 目标目录：$B_DIR"
count=0  # 统计创建的链接数
for file in "$A_DIR"/* "$A_DIR"/.[!.]*; do
    # 跳过不存在的文件（避免通配符匹配不到文件时的空值）
    [ -e "$file" ] || continue
    
    # 获取文件的basename（仅文件名，不含路径），确保链接名和源文件名一致
    filename=$(basename "$file")
    link_path="$B_DIR/$filename"
    
    # 如果目标目录已存在同名链接/文件，先提示并跳过（避免覆盖）
    if [ -e "$link_path" ]; then
        echo "⚠️  跳过：$link_path 已存在，不重复创建"
        continue
    fi
    
    # 创建软链接（使用绝对路径，避免路径失效）
    ln -s "$file" "$link_path"
    count=$((count + 1))
done

# 6. 执行完成提示
echo "✅ 执行完成！共创建 $count 个软链接"
echo "🔍 验证方法：执行 ls -l $B_DIR 查看链接指向"