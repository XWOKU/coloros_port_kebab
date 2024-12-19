import sys
import re
import os

STUB_METHOD = '''\
    .locals 1
    const/4 v0, 0x%s
    return v0
'''

STUB_VOID = '''\
    .locals 0
    return-void
'''

def patch_method_in_file(smali_path, method_set, return_type="true"):
    """修改指定smali文件中的方法返回值"""
    if not os.path.isfile(smali_path):
        print(f"----> Ignore patch: \"{os.path.basename(smali_path)}\" not found")
        return

    # 读取smali文件
    with open(smali_path, 'r') as f:
        smali = f.read()

    method_name = ''
    patched = ''
    overwriting = False

    # 根据return_type选择合适的返回值
    if return_type == "true":
        overvalue = '1'
    elif return_type == "false":
        overvalue = '0'
    elif return_type == "void":
        overvalue = '-1'
    else:
        print("Error: Invalid return type specified.")
        return

    for line in smali.splitlines():
        # 匹配方法定义行
        method_line = re.search(r'\.method\s+(?:(?:public|private)\s+)?(?:static\s+)?(?:final\s+)?([^\(]+)\(', line)
        if method_line:
            method_name = method_line.group(1)
            if method_name in method_set:
                overwriting = True
            patched += line + '\n'
        elif '.end method' in line:
            # 如果需要修改此方法，插入修改后的返回值
            if overwriting:
                overwriting = False
                if overvalue == '-1':
                    patched += STUB_VOID + line + '\n'
                    print(f"----> patched method in {smali_path}: {method_name} => void")
                else:
                    patched += (STUB_METHOD % overvalue) + line + '\n'
                    print(f"----> patched method in {smali_path}: {method_name} => " + ('true' if overvalue == '1' else 'false'))
            else:
                patched += line + '\n'
        else:
            # 非方法定义和结束的行保持不变
            if not overwriting:
                patched += line + '\n'

    # 将修改后的内容写回smali文件
    with open(smali_path, 'w') as f:
        f.write(patched)

def search_and_patch(smali_dir, keyword, return_type="true"):
    """在指定目录中搜索包含关键词的方法并修改返回值"""
    method_set = set()
    for root, _, files in os.walk(smali_dir):
        for file in files:
            if file.endswith(".smali"):
                smali_path = os.path.join(root, file)
                with open(smali_path, 'r') as f:
                    smali_content = f.read()

                # 查找包含关键词的方法
                for method_match in re.finditer(r'\.method\s+(?:(?:public|private)\s+)?(?:static\s+)?(?:final\s+)?([^\(]+)\(.*?\.end method', smali_content, re.DOTALL):
                    method_content = method_match.group(0)
                    if keyword in method_content:
                        method_name = re.search(r'\.method\s+(?:(?:public|private)\s+)?(?:static\s+)?(?:final\s+)?([^\(]+)\(', method_content).group(1)
                        method_set.add(method_name)
                        print(f"Found method '{method_name}' in file: {smali_path}")

                        # 调用方法修改函数
                        patch_method_in_file(smali_path, {method_name}, return_type)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patchmethod.py <smali_file> [method_names...]")
        print("Or: python3 patchmethod.py -d <directory> -k <keyword> -return <true|false|void>")
        return 1

    # 初始化默认返回值类型
    return_type = "true"

    # 检查参数中是否包含 -return
    if "-return" in sys.argv:
        return_index = sys.argv.index("-return") + 1
        if return_index < len(sys.argv):
            return_type = sys.argv[return_index]
        else:
            print("Error: Missing return type after -return.")
            return 1

    if "-d" in sys.argv and "-k" in sys.argv:
        # 使用目录搜索和关键词模式
        dir_index = sys.argv.index("-d") + 1
        keyword_index = sys.argv.index("-k") + 1

        if dir_index < len(sys.argv) and keyword_index < len(sys.argv):
            smali_dir = sys.argv[dir_index]
            keyword = sys.argv[keyword_index]
            search_and_patch(smali_dir, keyword, return_type)
        else:
            print("Error: Both -d <directory> and -k <keyword> are required.")
            return 1
    else:
        # 原始模式，直接对指定smali文件的特定方法进行修改
        smali_path = sys.argv[1]
        method_list = sys.argv[2:]
        if len(method_list) == 0:
            return 0
        method_set = set(method_list)
        patch_method_in_file(smali_path, method_set, return_type)

if __name__ == "__main__":
    main()
