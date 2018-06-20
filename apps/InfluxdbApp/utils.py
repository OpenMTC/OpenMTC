import distutils.command.sdist
import distutils.command.build_py
import os
import subprocess
import sys


def echo(msg, *args):
    if args:
        msg = msg % args
    sys.stdout.write(msg + "\n")


def get_packages(package, package_dir, excluded_list=None, included_list=None):
    included_list = included_list or []
    excluded_list = excluded_list or []

    try:
        root = package_dir[package]
    except KeyError:
        root = package_dir.get("", ".") + "/" + package

    if not os.path.exists(root):
        sys.stderr.write(
            "Directory for package %s does not exist: %s\n" % (package, root))
        sys.exit(1)

    def on_error(error):
        sys.stderr.write(
            "Error while collecting packages for %s: %s\n" % (package, error))
        sys.exit(1)

    packages = [package]

    r_prefix = len(root) + 1
    for path, dirs, files in os.walk(root, onerror=on_error):
        is_module = "__init__.py" in files and path != root
        excluded = any(map(lambda x: x in path, excluded_list))
        included = any(map(lambda x: x in path, included_list))
        if is_module and (not excluded or included):
            packages.append(package + "." + path[r_prefix:].replace("/", "."))

    return packages


def get_pkg_files(base_dir, name):
    package_files = []
    pkg_dir = os.path.join(base_dir, 'src', name)
    pkg_data_dir = os.path.join(pkg_dir, 'static')
    for (path, directories, filenames) in os.walk(pkg_data_dir):
        for filename in filenames:
            package_files.append(os.path.join(os.path.relpath(path, pkg_dir),
                                              filename))
    return package_files


def enable_init_files(init_dir, init_dist_files):
    for f in init_dist_files:
        os.chmod(os.path.join(init_dir, os.path.basename(f)), 0755)


def move_config_files(config_dir, config_files):
    for f in config_files:
        target_file = os.path.join(config_dir, f)
        if not os.path.exists(target_file):
            echo("Installing config file %s", target_file)
            os.rename(target_file + ".dist", target_file)
            # os.chmod(target_file, 0644)
        else:
            echo("Not overwriting config file %s", target_file)


def create_openmtc_user(db_dir=None, log_dir=None):
    try:
        from pwd import getpwnam
    except ImportError:
        print "Could not import the 'pwd' module. Skipping user management"
    else:
        # assuming DB_DIR was created by setup already
        try:
            pw = getpwnam('openmtc')
        except KeyError as e:
            try:
                # add system user openmtc:openmtc
                # useradd --system -UM openmtc
                useradd = "useradd --system -UM openmtc"
                retcode = subprocess.call(useradd, shell=True)
                if retcode:
                    raise Exception("Failed to add user 'openmtc'")
                pw = getpwnam('openmtc')
            except Exception as e:
                sys.stderr.write("Error creating user: %s\n" % (e, ))
                sys.exit(1)
        uid = pw.pw_uid
        gid = pw.pw_gid

        # set path permissions
        if db_dir:
            os.chown(db_dir, uid, gid)
        if log_dir:
            os.chown(log_dir, uid, gid)


class OpenMTCSdist(distutils.command.sdist.sdist):
    def make_release_tree(self, base_dir, files):
        distutils.command.sdist.sdist.make_release_tree(self, base_dir, files)

        script_name = os.path.basename(sys.argv[0])

        if script_name != "setup.py":
            os.rename(base_dir + "/" + script_name, base_dir + "/setup.py")
            self.filelist.files.remove(script_name)
            self.filelist.files.append("setup.py")


class OpenMTCSdistBinary(OpenMTCSdist, object):
    def make_release_tree(self, base_dir, files):
        super(OpenMTCSdistBinary, self).make_release_tree(base_dir, files)

        script_name = os.path.basename(sys.argv[0])

        build_py = self.get_finalized_command('build_py')
        build_py.compile = 1
        build_py.optimize = 2
        build_py.retain_init_py = 1
        build_py.build_lib = base_dir
        build_py.byte_compile(
            [base_dir + "/" + f for f in self.filelist.files if
             f != script_name and f.endswith(".py")])


class OpenMTCBuildPy(distutils.command.build_py.build_py):
    retain_init_py = 0

    def byte_compile(self, files):
        distutils.command.build_py.build_py.byte_compile(self, files)


class OpenMTCBuildPyBinary(OpenMTCBuildPy, object):
    retain_init_py = 0

    def byte_compile(self, files):
        super(OpenMTCBuildPyBinary, self).byte_compile(files)

        for f in files:
            if (f.endswith('.py') and (os.path.basename(f) != "__init__.py" or
                                       not self.retain_init_py)):
                os.unlink(f)
