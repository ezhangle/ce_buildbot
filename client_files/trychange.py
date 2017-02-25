#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
from tkinter import *


class PyTry:
    """
    This is a very simple program that presents a GUI of tickboxes for each valid platform/config that a repo can build.
    Platforms/configs that are required to be built before submission are read from the branch's buildbot_config.json,
    which must also be on the server for its counterpart (the repository's 'update' hook) to check.
    """
    def __init__(self, tkroot):
        self.buttons = {}
        self.frame = Frame(tkroot)
        self.frame.pack()

        self.data = {}
        self.branch = ''
        self.new_head = ''
        self.repository = ''
        self.sdk_repo_url = ''
        self.buildbot_url = ''
        self.targets = []
        self.configs = []
        self.checkboxes = {}

        os.chdir(args.repopath)

        self.read_repo_data()
        self.gather_data()
        self.create_grid()
        self.select_buttons()

    @staticmethod
    def fmt_name(**kwargs):
        """
        Since button names can be arbitrary strings, encode target/config properties.
        This avoids more hacky string parsing based on splitting at underscores etc.
        """
        return json.dumps(kwargs, sort_keys=True)

    def create_grid(self):
        """
        Create a grid of checkboxes for selecting which targets and configs to build.
        """
        row = 0
        col = 1
        for config in self.configs:
            print('config = {}'.format(config))
            Label(self.frame, text=config).grid(row=row, column=col)
            col += 1

        row += 1
        for target in self.targets:
            col = 0
            Label(self.frame, text=target).grid(row=row, column=col)

            col += 1
            for config in self.configs:
                name = self.fmt_name(target=target, config=config)
                self.checkboxes[name] = Checkbutton(self.frame, variable=self.buttons[name])
                self.checkboxes[name].grid(row=row, column=col)
                col += 1
            row += 1

        Button(self.frame, text='Launch', command=self.launch_builds).grid(column=1)

    def launch_builds(self):
        """
        Send the patch to the buildbot server and instruct it to build the selected configurations. This uses
        the buildbot package, which must be installed from PIP (or frozen into an executable and stored locally).
        """
        for buttonname in self.buttons:
            if not self.buttons[buttonname].get():
                continue

            data = json.loads(buttonname)
            cmd = ['buildbot', 'try', '--connect=pb', '--master={}'.format(self.buildbot_url),
                   '--username=build', '--passwd=build', '--vc=git',
                   '--builder={}'.format(self.get_buildername(data['target']))]

            prop_list = ['branch={}'.format(self.branch),
                         'repository={}'.format(self.repository),
                         'head_ref={}'.format(self.new_head),
                         'sdk_repo_url={}'.format(self.sdk_repo_url)]
            for k in data:
                prop_list.append('{}={}'.format(k, data[k]))
            cmd.append('--properties={}'.format(','.join(prop_list)))

            print('Running "{}"'.format(' '.join(cmd)))
            subprocess.call(cmd)

    @staticmethod
    def get_buildername(target):
        if target.startswith('win'):
            return 'compile_win'
        elif target.startswith('linux'):
            return 'compile_linux'
        else:
            return 'nothing'

    def select_buttons(self):
        """
        Tick the boxes corresponding to the required targets and configurations for this branch.
        """
        for target in self.targets:
            for config in self.configs:
                name = self.fmt_name(target=target, config=config)
                if config in self.data[target]:
                    self.checkboxes[name].select()

    def read_repo_data(self):
        """
        Read data about a repository by running git commands an parsing their output.
        """
        raw_output = subprocess.check_output(['git', 'branch']).decode()
        self.branch = raw_output.strip().split(' ')[1]  # "* release* -> "release"
        print('Found local branch "{}".'.format(self.branch))

        raw_output = subprocess.check_output(['git', 'remote', 'get-url', 'origin']).decode()
        self.repository = raw_output.strip().replace('git@', '')   # 'git@' is awkward to pass.
        print('Found repository "{}".'.format(self.repository))

        raw_output = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode()
        self.new_head = raw_output.strip()
        print('Head ref "{}".'.format(self.new_head))

    def gather_data(self):
        """
        Read information from the buildbot config file and store the data for setting up the GUI later.
        """
        with open('buildbot_config.json') as cfg:
            self.data = json.load(cfg)

        self.targets = self.data['targets']
        self.configs = self.data['configs']
        self.buildbot_url = self.data['buildbot_url']
        self.sdk_repo_url = self.data['sdk_repo_url']

        for target in self.targets:
            for config in self.configs:
                name = self.fmt_name(target=target, config=config)
                self.buttons[name] = IntVar()


if __name__ == '__main__':
    root = Tk()

    parser = argparse.ArgumentParser('Try a change against a buildbot server.')
    parser.add_argument('--repopath', required=True, help='Path to the repository that you want to build.')
    args = parser.parse_args()

    d = PyTry(root)
    root.mainloop()
