
from buildbot.plugins import *


CMAKE_GENERATORS = {'win_x86': 'Visual Studio 14 2015',
                    'win_x64': 'Visual Studio 14 2015 Win64',
                    'linux_x64_gcc': 'Unix Makefiles',
                    'linux_x64_clang': 'Unix Makefiles'}


@util.renderer
def compute_build_properties(props):
    """
    Set the build properties required by the target, for instance; the path to the toolchain file.
    :param props: Current build properties.
    """
    build_properties = {
        'repository': 'git://github.com/CRYTEK-CRYENGINE/{}.git'.format(props.getProperty('project')),
        'cmakegenerator': CMAKE_GENERATORS.get(props.getProperty('target'))
    }

    # Put this here to avoid PEP8 shenanigans.
    win_link_sdk_cmd = r'rmdir %(prop:project)s\Code\SDKs & mklink /J %(prop:project)s\Code\SDKs SDKs'

    if props.getProperty('target') == 'win_x86':
        build_properties.update({
            'vsplatform': 'Win32',
            'cmake_sln_tag': 'Win32',
            'toolchain_path': 'Tools/CMake/toolchain/windows/WindowsPC-MSVC.cmake',
            'link_sdk_cmd': util.Interpolate(win_link_sdk_cmd)
        })
    elif props.getProperty('target') == 'win_x64':
        build_properties.update({
            'vsplatform': 'x64',
            'cmake_sln_tag': 'Win64',
            'toolchain_path': 'Tools/CMake/toolchain/windows/WindowsPC-MSVC.cmake',
            'link_sdk_cmd': util.Interpolate(win_link_sdk_cmd)
        })
    elif props.getProperty('target') == 'linux_x64_gcc':
        build_properties.update({
            'toolchain_path': 'Tools/CMake/toolchain/linux/Linux_GCC.cmake',
            'link_sdk_cmd': ['ln', '-sfn', 'SDKs', util.Interpolate('%(prop:project)s/Code/SDKs')]
        })
    elif props.getProperty('target') == 'linux_x64_clang':
        build_properties.update({
            'toolchain_path': 'Tools/CMake/toolchain/linux/Linux_Clang.cmake',
            'link_sdk_cmd': ['ln', '-sfn', 'SDKs', util.Interpolate('%(prop:project)s/Code/SDKs')]
        })
    return build_properties


def add_common_steps(factory):
    """
    Add steps to the provided factory that are common to both Windows and Linux builds.
    :param factory: Factory to which the steps should be added.
    """
    factory.addStep(steps.SetProperties(properties=compute_build_properties))
    factory.addStep(steps.Git(name='get code',
                              alwaysUseLatest=True,
                              repourl=util.Interpolate('%(prop:repository)s'),
                              branch=util.Interpolate('%(prop:branch)s'),
                              mode='incremental',
                              workdir=util.Interpolate('build/%(prop:project)s')))
    factory.addStep(steps.ShellCommand(name='link SDKs',
                                       command=util.Property('link_sdk_cmd')))
    factory.addStep(steps.CMake(name='configure',
                                path=util.Interpolate('../%(prop:project)s'),
                                generator=util.Interpolate('%(prop:cmakegenerator)s'),
                                options=[util.Interpolate('-DCMAKE_TOOLCHAIN_FILE=%(prop:toolchain_path)s')],
                                workdir=util.Interpolate('build/%(prop:target)s_%(prop:config)s')))


def get_compile_win_factory():
    factory = util.BuildFactory()
    add_common_steps(factory)
    factory.addStep(steps.MsBuild14(mode='build',
                                    platform=util.Interpolate('%(prop:vsplatform)s'),
                                    config=util.Interpolate('%(prop:config)s'),
                                    projectfile=util.Interpolate('CryEngine_CMake_%(prop:cmake_sln_tag)s.sln'),
                                    workdir=util.Interpolate('build/%(prop:target)s_%(prop:config)s')))
    return factory
