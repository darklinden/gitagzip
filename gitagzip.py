#!/usr/bin/env python

import subprocess
import os
import shutil
import errno
import sys

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

def touch_file(path, idx):
    p = os.path.join(path, idx + ".txt")
    f = open(p, "wb")
    f.write(idx)
    f.close()

def make_test_commits(path):

    os.chdir(path)

    idx = 0
    while idx < 100:
        touch_file(path, str(idx))
        idx += 1

        print(run_cmd(['git', 'add', '--all', '.']))
        print(run_cmd(['git', 'commit', '-m', "\"" + str(idx) + "\""]))

    print("make test commit Done")

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

def get_file_diff(commit1, commit2):
    ls = run_cmd(['git', 'diff', '--name-status', commit1, commit2])
    lines = ls.split("\n")

    ret = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if len(line.strip()) > 0:
            sl = line.split("\t")
            file = sl[-1]
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

    des_folder = des_path

    prefix_dir, file_name = os.path.split(sub_path)
    if len(prefix_dir) > 0:
        des_folder += "/" + prefix_dir

    mkdir_p(des_folder)

    shutil.copy(os.path.join(src_path, sub_path), des_folder + "/" + file_name)

def copy_diffs(src_path, des_path, diffs):
    if os.path.isdir(des_path):
        shutil.rmtree(des_path)
    os.mkdir(des_path)

    idx = 0
    while idx < len(diffs):
        file = diffs[idx]
        path_copy(src_path, des_path, file)
        idx += 1

def zip_tag_diffs(path):

    parent_path, src = os.path.split(path)

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

            diffs = get_file_diff(start_commit, end_commit)

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

def __main__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("gitagzip.py", "/usr/local/bin")
        return

    path = ""
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        return

    if len(path) == 0:
        print("using gitagzip [git-path] to zip git tag diffs")
        print("using gitagzip test to make test git repository")
        return

    if path == "test":
        path = os.getcwd()
        path += "/git_test_repo"
        mkdir_p(path)
        os.chdir(path)
        os.system("git init")
        make_test_commits(path)
    else:
        if path[0] != "/":
            path = os.getcwd() + "/" + path
        zip_tag_diffs(path)

__main__()
