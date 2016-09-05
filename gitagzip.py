#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os
import shutil
import errno
import sys

reload(sys)
sys.setdefaultencoding('utf8')

def run_cmd(cmd):
    print("run cmd: " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out

def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    print("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])

def get_git_tags():

    tags = run_cmd(['git', 'tag', '--list'])
    tag_list = tags.split("\n")

    ret = []
    idx = 0
    while idx < len(tag_list):
        tag = tag_list[idx]

        if len(tag.strip()) > 0:
            commit = run_cmd(['git', 'rev-list', '-n', '1', tag]).strip()
            obj = {}
            obj["tag"] = tag
            obj["commit"] = commit
            ret.append(obj)
        else:
            tag_list.remove(tag)

        idx += 1

    return ret

def get_file_diff(commit1, commit2, folders):
    ls = run_cmd(['git', 'diff', '--name-status', commit1, commit2])
    lines = ls.split("\n")

    ret = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if len(line.strip()) > 0:
            sl = line.split("\t")
            act = sl[0]
            file = sl[-1]

            if act == "A" or act == "M":
                if len(folders) > 0:
                    hasPrefix = False
                    for p in folders:
                        if file.startswith(p):
                            hasPrefix = True
                            break

                    if not hasPrefix:
                        idx += 1
                        continue

                ret.append(file)

        idx += 1

    return ret

def mkdir_p(path):
    # print("mkdir_p: " + path)
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def path_copy(src_path, des_path, sub_path):

    # print("path_copy")
    # print("src_path: " + src_path)
    # print("des_path: " + des_path)
    # print("sub_path: " + sub_path)

    des_folder = des_path

    prefix_dir, file_name = os.path.split(sub_path)
    if len(prefix_dir) > 0:
        des_folder = os.path.join(des_folder, prefix_dir)

    mkdir_p(des_folder)

    print("des_folder: " + des_folder)

    cp_src = os.path.join(src_path, sub_path)
    cp_des = os.path.join(des_path, sub_path)

    shutil.copy(cp_src, cp_des)

def copy_diffs(src_path, des_path, diffs):
    if os.path.isdir(des_path):
        shutil.rmtree(des_path)
    os.mkdir(des_path)

    idx = 0
    while idx < len(diffs):
        file = diffs[idx]

        path_copy(src_path, des_path, file)
        idx += 1

def zip_tag_diffs(path, folders):

    if path[-1] == "/":
        path = path[:-1]

    parent_path, src = os.path.split(path)

    print("zip_tag_diffs parent_path: " + parent_path)
    print("zip_tag_diffs src: " + src)
    os.chdir(path)
    tag_list = get_git_tags()

    idx = 0
    jdx = 0

    while idx < len(tag_list) - 1:

        jdx = idx + 1
        while jdx < len(tag_list):

            os.chdir(path)

            start_tag = tag_list[idx]["tag"]
            start_commit = tag_list[idx]["commit"]

            end_tag = tag_list[jdx]["tag"]
            end_commit = tag_list[jdx]["commit"]

            print("zip diff: " + start_tag + "_" + end_tag)

            print(run_cmd(['git', 'checkout', end_commit]))

            diffs = get_file_diff(start_commit, end_commit, folders)

            des_folder = parent_path + "/" + start_tag + "_" + end_tag

            copy_diffs(path, des_folder, diffs)

            os.chdir(des_folder)
            print("cd " + os.getcwd())

            cmd = "zip -r ../" + start_tag + "_" + end_tag + ".zip *"
            os.system(cmd)

            shutil.rmtree(des_folder)

            jdx += 1

        idx += 1

    print("zip git tag diffs Done")

def git_get_current_commit():
    line = ""
    ls = run_cmd(['git', 'show', '-s'])
    lines = ls.split("\n")
    if len(lines) > 0:
        line = lines[0]
        line = line.strip()
        line = line.strip("commit")
        line = line.strip()
    return line

def zip_commit_diffs(path, folders, start_commit, end_commit):
    print("zip_commit_diffs start commit: " + start_commit)
    print("zip_commit_diffs end commit: " + end_commit)

    if path[-1] == "/":
        path = path[:-1]

    parent_path, src = os.path.split(path)

    print("zip_tag_diffs parent_path: " + parent_path)
    print("zip_tag_diffs src: " + src)

    os.chdir(path)

    print("zip diff: " + start_commit + " - " + end_commit)

    print(run_cmd(['git', 'checkout', end_commit]))

    diffs = get_file_diff(start_commit, end_commit, folders)

    des_folder = parent_path + "/B" + start_commit[:7] + "_" + end_commit[:7]

    copy_diffs(path, des_folder, diffs)

    os.chdir(des_folder)
    print("cd " + os.getcwd())

    cmd = "zip -r ../B" + start_commit[:7] + "-" + end_commit[:7] + ".zip *"
    os.system(cmd)

    shutil.rmtree(des_folder)

    print("zip git commit diffs Done")

def cmd_getargs():

    arg_dict = {}
    arg_list = []

    tmp_key = ""
    tmp_value = ""

    idx = 0
    while idx < len(sys.argv):
        single_arg = sys.argv[idx]

        if single_arg[0] == '-':
            if len(tmp_key) > 0 and len(tmp_value) == 0:
                if arg_dict.has_key(tmp_key):
                    if tmp_key in arg_list:
                        obj = arg_dict[tmp_key]
                        obj.append(tmp_value)
                        arg_dict[tmp_key] = obj
                    else:
                        obj = []
                        obj.append(arg_dict[tmp_key])
                        obj.append(tmp_value)
                        arg_dict[tmp_key] = obj
                        arg_list.append(tmp_key)
                else:
                    arg_dict[tmp_key] = tmp_value
            tmp_key = single_arg[1:]
        else:
            tmp_value = single_arg.decode("utf-8")

        if tmp_key == "":
            tmp_value = ""
            idx += 1
            continue

        if len(tmp_key) > 0 and len(tmp_value) > 0:
            if arg_dict.has_key(tmp_key):
                if tmp_key in arg_list:
                    obj = arg_dict[tmp_key]
                    obj.append(tmp_value)
                    arg_dict[tmp_key] = obj
                else:
                    obj = []
                    obj.append(arg_dict[tmp_key])
                    obj.append(tmp_value)
                    arg_dict[tmp_key] = obj
                    arg_list.append(tmp_key)
            else:
                arg_dict[tmp_key] = tmp_value

            tmp_key = ""
            tmp_value = ""

        idx += 1

    return arg_dict

def __main__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("gitagzip.py", "/usr/local/bin")
        return

    if len(sys.argv) < 2:
        print("using gitagzip [git-path] [-l] to list all tags")
        print("using gitagzip [git-path] [-f folder] to zip git tag diffs")
        print("using gitagzip [git-path] [-f folder] [-s start commit] [-e end commit] to zip git commit diffs")
        return

    path = sys.argv[1]

    if str(path).startswith("-"):
        path = os.getcwd()

    if not str(path).startswith("/"):
        path = os.path.join(os.getcwd(), path)

    os.chdir(path)

    args = cmd_getargs()

    if args.has_key("l"):
        print("list all tags in [" + os.getcwd() + "]:")
        tag_list = get_git_tags()
        idx = 0
        while idx < len(tag_list):
            tag_obj = tag_list[idx]
            print("\ttag:\t" + tag_obj["tag"] + "\tcommit:\t" + tag_obj["commit"])
            idx += 1
        print("Done")
        return

    folders = []

    arg_folders = args.get("f", [])
    if not isinstance(arg_folders, list):
        tmp = []
        tmp.append(arg_folders)
        arg_folders = tmp

    idx = 0
    while idx < len(arg_folders):
        af = arg_folders[idx]
        if str(af).startswith("/"):
            af = af[len(path) + 1:]
        folders.append(af)
        idx += 1

    run_cmd(['git', 'config', '--global', 'core.quotepath', 'off'])

    if args.has_key("s"):
        start_commit = args["s"]
        end_commit = ""
        if args.has_key("e"):
            end_commit = args["e"]
        else:
            end_commit = git_get_current_commit()

        zip_commit_diffs(path, folders, start_commit, end_commit)
    else:
        zip_tag_diffs(path, folders)

__main__()
