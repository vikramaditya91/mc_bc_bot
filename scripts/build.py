# -*- coding: utf-8 -*-
"""Build script.

This contains sub-project entry point to build and release the package.


"""
import logging
import os
import sys
import os.path as op
import platform
import subprocess
import tempfile
import shutil
import re
import time
if sys.version_info[0] >= 3:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve
from contextlib import contextmanager
from distutils.version import LooseVersion
from distutils import dir_util

THIS_DIR = op.abspath(op.dirname(__file__))
PKG_DIR = op.abspath(op.join(THIS_DIR, os.pardir))
OUT_DIR = op.join(PKG_DIR, '__build_artifacts__')
if not op.exists(OUT_DIR):
    os.makedirs(OUT_DIR)
PROJECT_NAME = "mc_bc_bot"


logger = logging


# The miniconda installer to use in case the system does not have th minimal
# requirements
CONDA_INSTALLER = {
    'windows': 'https://repo.continuum.io/miniconda/Miniconda3-4.5.4-Windows-x86_64.exe',

    # Last version known to be working on centos 6.0
    'linux': 'https://repo.continuum.io/miniconda/Miniconda3-4.5.4-Linux-x86_64.sh'
}


logger.info("Current python version {0}".format(sys.version))
if LooseVersion(sys.version) < LooseVersion('2.7'):
    """Extend subprocess module with the call method that was only introduced
    in python 2.7.
    """
    def subprocess_call(*args, **kwargs):
        return subprocess.Popen(*args, **kwargs).communicate()[0]
        # return subprocess.Popen(*args, **kwargs).wait()
    subprocess.call = subprocess_call


def define_display():
    """Set the display variable if not set."""
    if not "DISPLAY" in os.environ:
        os.environ["DISPLAY"] = ":0"


class CondaError(RuntimeError):
    """Custom error to enable error filtering."""
    pass


def run_command(command, command_inputs=None, cwd=None):
    """Simple wrapper around system command call.

    :param command:
        str, the system command to execute.

    :param command_inputs:
        list, of the command input to send sequentially.

    :param cwd:
        (int, str, str), a tuple of error code, out string and error string
        outputs.

    """
    logger.debug("Executing: {0} with {1}".format(command, command_inputs))
    if cwd is None:
        cwd = THIS_DIR

    if platform.system() == "Windows":
        shell_executable = None
    else:
        shell_executable = '/bin/bash'

    process = subprocess.Popen(
        "{0}".format(command),
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=cwd,
        executable=shell_executable
    )

    out, err = ('', '')
    if hasattr(command_inputs, '__iter__'):
        for command_input in command_inputs:
            if sys.version_info[0] >= 3:
                command_input = command_input.encode('utf-8')
            p_result = process.communicate(command_input)
            if sys.version_info[0] >= 3:
                p_result = [x.decode('ascii') for x in p_result]
            out += p_result[0]
            err += p_result[1]
    else:
        out, err = process.communicate('')
        if sys.version_info[0] >= 3:
            out = out.decode('ascii')
            err = err.decode('ascii')

    return process.returncode, out, err


def get_miniconda_from_web(archive_url, tmp_dir=None):
    """Download miniconda archive from the web, return downloaded file."""
    logger.info("Pull miniconda from {0} in {1}..."
                .format(archive_url, tmp_dir))
    if tmp_dir is None:
        tmp_dir = tempfile.gettempdir()
    if platform.system() == "Windows":
        tmp_file = op.join(tmp_dir, "miniconda_install.exe")
    else:
        tmp_file = op.join(tmp_dir, "miniconda_install.sh")

    if not op.exists(tmp_file):
        urlretrieve(archive_url, tmp_file)
        if not op.exists(tmp_file):
            raise CondaError("Could not download {0}".format(archive_url))

    return tmp_file


def install_miniconda_linux(file_archive, location):
    """ Install miniconda archive from source in temp location.

    :param file_archive:
        str, path to miniconda shell archive.

    :param location:
        str, path to folder to use.
    """
    # Create one single temp dir per execution
    location = op.join(location, 'build_env_linux')
    if op.exists(location):
        rmtree(location)

    # Fix the execution flag
    logger.info("Fix exec flag...")
    code, out, err = run_command('chmod +x "{0}"'.format(file_archive))
    if err != '' or code != 0:
        raise CondaError("Could not fix permission on {0}, error: {1} code {2}"
                         .format(tempfile, err, code))

    # Install the root env in tmp
    logger.info('Installing miniconda in "{0}"...'.format(location))
    code, out, err = run_command(command='{} -b -p {} -u'.format(file_archive, location))

    if not err.startswith('Python') or code != 0:
        raise CondaError('Could not install "{0}", error {1} code {2}'
                         .format(file_archive, err, code))

    # Make it known on the system with precedence to override other install
    sys.path.insert(0, location)

    return location


def install_miniconda_windows(file_archive, location):
    """ Install miniconda archive from source in temp location.

    :param file_archive:
        str, path to miniconda executable archive.

    :param location:
        str, path to folder to use.
    """
    # Create one single temp dir per execution
    location = op.join(location, 'build_env_windows')
    if op.exists(location):
        rmtree(location)

    # Install the root env in tmp
    logger.info("Installing miniconda in {0}...".format(location))
    code, out, err = run_command(
        command="{} /AddToPath=0 /RegisterPython=0 /S /D={}".format(file_archive, location),
        command_inputs=['\n']
    )
    if err != '' or code != 0:
        raise CondaError("Could not install {0}, error {1} code {2}"
                         .format(file_archive, err, code))

    # Make it known on the system with precedence to override other install
    sys.path.insert(0, location)

    return location


def install_conda_command():
    """ Install conda command in current python interpreter."""
    logger.info("Install conda command in current environement...")
    code, out, err = run_command("pip install conda")
    if err != '' or code != 0:
        raise CondaError("Could not install conda command, {0} error: {1} code "
                         "{2}".format(out, err, code))


def create_or_update_root_environment(environment_settings, location):
    """Ensure we get a distribution from which we can create environments.

    :param environment_settings:
        dict, containing the list of necessary module statuses.
    """
    # if not environment_settings["conda"]:
    #     if not environment_settings["pip"]:

    # Then we need a basic installation
    logger.info("Root environment is missing conda and pip.")

    if platform.system() == "Windows":
        file_archive = get_miniconda_from_web(
            archive_url=CONDA_INSTALLER['windows'], tmp_dir=location
        )

        root_interpreter_path = install_miniconda_windows(
            file_archive=file_archive, location=location
        )
    else:
        file_archive = get_miniconda_from_web(
            archive_url=CONDA_INSTALLER['linux'], tmp_dir=location
        )

        root_interpreter_path = install_miniconda_linux(
            file_archive=file_archive, location=location
        )
    return root_interpreter_path


def get_python_bin_from_env(env_prefix):
    """Return the platform independent location of the python executable.

    :param env_prefix:
        str, the path to the environment to use.

    :return python_bin:
        str, the path to the executable python binary.
    """
    if platform.system() == "Windows":
        python_bin = op.join(env_prefix, 'python.exe')
    else:
        python_bin = op.join(env_prefix, 'bin', 'python')
    return python_bin


def run_python(env_prefix, args, cwd=None):
    """ Execute a platform independent python command.

    :param env_prefix:
        Python executable prefix to use to run the command.

    :param args:
        Optional python arguments.

    :param cwd:
        The current working directory.

    :return:
        The result of the python command.

    """
    if not cwd:
        cwd = THIS_DIR
    command = "{0} {1}".format(get_python_bin_from_env(env_prefix), args)
    logger.info(command)
    return run_command(command, cwd=cwd)


def install_pip_dependencies(python_prefix):
    """ Install pip dependencies.

    In some case the package dependencies are only available through pip. In
    such case this function enables the user to install the pip dependencies in
    the corresponding python environment pointed by python_prefix.

    :param python_prefix:
        The root folder of the python environment to use.

    """
    pip_req_dir = op.join(THIS_DIR)

    if platform.system() == "Windows":
        pip_req_file = op.join(pip_req_dir, 'pip_req_windows.txt')
    else:
        pip_req_file = op.join(pip_req_dir, 'pip_req_linux.txt')

    if op.exists(pip_req_file):
        logger.info("Installing additional dependencies through pip ...")
        code, out, err = run_python(python_prefix, "-m pip install -r {0}"
                                    .format(pip_req_file))
        logger.info(out)
        if code != 0:
            logger.error(err)
            raise CondaError("Could not install some dependencies")


def run_local_env_command(python_prefix, command, cwd=THIS_DIR):
    """Execute a local python env command using bin from python_prefix.

    """
    if platform.system() == "Windows":
        command_exec = command.split(' ')[0]
        command_trail = command[len(command_exec):]
        if '.' not in command_exec:
            command_exec += '.exe'
        local_exec = op.join(python_prefix, "Scripts", command_exec)
        localized_command = "{0}{1}".format(local_exec, command_trail)
    else:
        python_exec = op.join(python_prefix, "bin", "python")
        localized_command = "{0} -m {1}".format(python_exec, command)
    code, out, err = run_command(localized_command, cwd=cwd)
    logger.info(out)
    if 'error' in err or code != 0:
        logger.error(err)
        raise CondaError("Command {0} returned error code {1}, error: {2}"
                         .format(command, code, err))


def make_conda_env(python_prefix):
    """Create a conda environment based on package definition.

    Since conda does not support creating environment based on package
    requirements (yet see also feature request:
    https://github.com/conda/conda/issues/6788), we do it here.
    This function will create a conda environment containing the necessary
    dependencies to test and release the current project.

    :param python_prefix:
        The path where to create the python environment.

    """
    if platform.system() == "Windows":
        requirement_file = "conda_req_windows.txt"
    else:
        requirement_file = "conda_req_linux.txt"

    logger.info("Installing conda requirements ...")
    conda_req_file = op.join(THIS_DIR, requirement_file)
    logger.info("Installing conda packages from {0} in {1}"
                .format(conda_req_file, python_prefix))

    command = "conda install --file {0} -p {1} -y"\
        .format(conda_req_file, python_prefix)
    run_local_env_command(python_prefix, command)

    # Install pip dependencies after conda requirements.
    install_pip_dependencies(python_prefix)

    return python_prefix


def make_conda_package(python_install_path):
    logger.info("Making conda package...")
    conda_command = op.join(python_install_path, 'Scripts', 'conda')
    dist_folder = op.join(OUT_DIR, 'dist', 'conda')
    if op.exists(dist_folder):
        rmtree(dist_folder)

    conda_recipe_dir = "./"
    python_version = "2.7"
    cmd = "{0} build {1} --python {2} --channel conda-forge --no-anaconda-upload --output-folder={3}".format(conda_command, conda_recipe_dir, python_version, dist_folder)
    code, out, err = run_command(cmd, cwd=THIS_DIR)
    logger.info(out)
    if code != 0:
        logger.error(err)
        raise RuntimeError("!!! Conda build failed to run")



def rmtree(path):
    def onerror(func, path, exc_info):
        """
        Error handler for ``shutil.rmtree``.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.
        Usage : ``shutil.rmtree(path, onerror=onerror)``
        """
        import stat
        if not os.access(path, os.W_OK):
            # Is the error an access error ?
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            logger.warning("Could not remove file: {0}".format(path))

    if op.exists(path):
        shutil.rmtree(path, onerror=onerror)


def check_pip():
    """Check if pip is accessible with the current interpreter.

    :return:
        boolean, True if pip is importable, false otherwise.
    """
    code, out, err = run_command("python -m pip --version")
    if ("No module named" in out) or (code != 0):
        return False
    return True


def check_pipenv():
    """Check if pipenv is accessible with the current interpreter.

    :return:
        boolean, True if pipenv is importable, false otherwise.
    """
    code, out, err = run_command("python -m pipenv --version")
    if "No module named" in out or code != 0:
        return False
    return True


def check_conda():
    """Check if conda is accessible with the current interpreter.

    :return:
        boolean, True if conda is importable, false otherwise.
    """
    code, out, err = run_command("python -m conda --version")
    if err.startswith('conda '):
        return True
    return False


def get_environment_settings():
    """Return a dict condaining the status of different packages needed."""
    env = {
        "pip": check_pip(),
        "pipenv": check_pipenv(),
        "conda": check_conda()
    }
    logger.debug("Current python env: {0}".format(env))
    return env


def desired_python_in_conda():
    u"""
    Searches through the conda requirement to obtain the right version of python.
    As we might have python 2 and 3 versions running at the same time,
    this helps to set a different _tmp_conda_env_<python_main_ver>
    :return: The major version of python (2 or 3)

    If for some reason it could not find the python version,
    it returns that the python version is 2 as a failsafe
    """
    if platform.system() == "Windows":
        requirement_file = "conda_req_linux.txt"
    else:
        requirement_file = "conda_req_windows.txt"
    conda_req_file = op.join(THIS_DIR, os.pardir, requirement_file)

    with open(conda_req_file) as conda_req:
        conda_req_list = conda_req.read().split("\n")
    for item in conda_req_list:
        if "python==" in item:
            python_item = re.search('python==\d', item)
            return python_item.group()[-1]
    return "2" #Fail-safe


@contextmanager
def conda_env():
    """ Create a temporary python environment to run the packaging.

    This context manager will provide a safe wrapper around the temporary
    python distribution. The python distribution is built every time based on
    package requirements and disposed (folder deleted) on exit.

    :return:
        tmp_conda the path to the temporary python environment.
    """
    tmp_conda = op.join(OUT_DIR, '_tmp_conda_env_3')
    logger.info("Temporary python environment will be located in : {0}"
                .format(tmp_conda))

    original_environ = os.environ.copy()
    if platform.system() == "Windows":
        path_to_add = op.join(tmp_conda, 'build_env_windows', 'Library', 'bin')
        if 'PATH' in original_environ.keys():
            original_path = original_environ['PATH']
            os.environ['PATH'] = path_to_add + os.pathsep + original_path
        else:
            os.environ['PATH'] = path_to_add

    # Required for unittests with the CLI which are spawned in a new shell
    os.environ['PYTHONPATH'] = op.join(OUT_DIR, '..')

    try:
        if not op.exists(tmp_conda):
            os.makedirs(tmp_conda)
            env_settings = get_environment_settings()
            root_interpreter_path = create_or_update_root_environment(
                env_settings, tmp_conda
            )

            try:
                yield make_conda_env(root_interpreter_path)
            except CondaError as e:
                logger.error("Could not setup conda env. Reason: {0}. Aborting."
                             .format(e.args[0]))
        else:
            # If it exists we assume the env is ok
            logger.warning(
                "A local environment exists already! We will assume it is correct."
            )
            logger.warning("Skipping create_or_update_root_environment")
            if platform.system() == "Windows":
                yield op.join(tmp_conda, 'build_env_windows')
            else:
                yield op.join(tmp_conda, 'build_env_linux')
    finally:
        os.environ = original_environ


def run_tests(python_prefix):
    all_err = ""
    logger.info("Running tests using python {0} ...".format(python_prefix))
    test_results = op.join(OUT_DIR, 'testresults')
    if not op.exists(test_results):
        os.makedirs(test_results)
    if platform.system() == "Windows":
        coverage_exec = op.join(python_prefix, 'Scripts', 'coverage')
    else:
        coverage_exec = 'coverage'
    setup_file = op.join(PKG_DIR, 'setup.py')
    # command = "{0} run {1} test 2>&1".format(coverage_exec, setup_file)
    command = "{0} run --source={1}/project_dir {2} test 2>&1".format(coverage_exec, PKG_DIR, setup_file)
    logger.info("Test command : {0}".format(command))
    run_local_env_command(python_prefix, command, cwd=PKG_DIR)

    # Reporting
    command = "{0} report -m".format(coverage_exec)
    run_local_env_command(python_prefix, command, cwd=PKG_DIR)

    # Build html report
    command = "{0} html -d {1}".format(coverage_exec, op.join(OUT_DIR, "test_report"))
    run_local_env_command(python_prefix, command, cwd=PKG_DIR)

    # Build XML report
    command = "{0} xml -o {1}".format(coverage_exec, op.join(OUT_DIR, "coverage.xml"))
    run_local_env_command(python_prefix, command, cwd=PKG_DIR)


def execute_bot(python_prefix):
    """Build up the application with pyinstaller.

    Return the folder in which we generate the binaries.
    """
    get_python_bin_from_env(env_prefix=python_prefix)
    command = "{0} ../".format(coverage_exec, PKG_DIR, setup_file)
    logger.info("Test command : {0}".format(command))
    run_local_env_command(python_prefix, command, cwd=PKG_DIR)


def clean():
    """Clean up some packaging files."""
    folders_to_clean = [
        op.join(THIS_DIR, '..', 'dist'),
        op.join(THIS_DIR, '..', 'build'),
        op.join(THIS_DIR, '..', 'numeca_admin_tool.egg-info'),
    ]
    for folder in folders_to_clean:
        if op.exists(folder):
            rmtree(folder)


def release_environment(python_prefix):
    """ Export the temporary python environment into local build artifact.

    :param python_prefix:
    :return:
    """
    env_dir = op.join(OUT_DIR, "python_distribution")
    shutil.copytree(python_prefix, env_dir)


def do_cleanup(python_prefix):
    code, out, err = run_python(python_prefix, "setup.py clean", cwd=PKG_DIR)
    if code != 0:
        raise RuntimeError("setup.py clean failed to run!")


def main():
    with conda_env() as env_prefix:
        logger.info("Using python environment: {0}".format(env_prefix))
        try:
            # run_tests(env_prefix)
            execute_bot(env_prefix)
            clean()
            return 0
        except Exception as e:
            logger.error("At least one error occured during building.")
            logger.error("Error : {0}".format(e))
            return 1


def configure_logging():
    """Configure logger."""
    logger = logging.getLogger("Builder")
    logger.setLevel(logging.INFO)
    log_format = "%(levelname)s %(asctime)-15s %(threadName)s %(message)s"
    formatter = logging.Formatter(log_format, None)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger.propagate = False
    # from distutils import log
    # log.set_verbosity(log.DEBUG)
    # os.environ["DISTUTILS_DEBUG"] = "1"
    return logger


if __name__ == '__main__':
    define_display()
    logger = configure_logging()
    sys.exit(main())
