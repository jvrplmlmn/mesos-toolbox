#!/usr/bin/python
import os, time
from lib.config import Config
from lib.configs.mesos_config import MesosConfig
from lib.utils import Utils

LOG = MesosConfig.setup(__file__)

def ensure_sources():
    path = MesosConfig.mesos_repository_dir()
    if os.path.isdir("{}/.git".format(path)):
        LOG.info("Updating sources for {}...".format(MesosConfig.mesos_git_repository()))
        result = Utils.cmd("cd {} && git fetch origin".format(path))
        if result['ExitCode'] == 0:
            LOG.info("Done.")
            return True
        else:
            Utils.print_result_error(LOG, "Failed.", result)
            return False
    else:
        LOG.info("No sources for {} found. Cloning...".format(MesosConfig.mesos_git_repository()))
        result = Utils.cmd("cd {} && git clone {} .".format(path, MesosConfig.mesos_git_repository()))
        if result['ExitCode'] == 0:
            LOG.info("Done.")
            return True
        else:
            Utils.print_result_error(LOG, "Failed.", result)
            return False

def ensure_deb_packaging():
    path = MesosConfig.deb_packaging_repository_dir()
    if os.path.isdir("{}/.git".format(path)):
        LOG.info("Updating sources for {}...".format(MesosConfig.deb_packaging_repository()))
        # TODO: compare given sha and repo sha
        # TODO: if different, reset, pull, checkout
        # TODO: apply patches for deb-packaging, if any...
        LOG.info("Done.")
        return True
    else:
        LOG.info("No sources for {} found. Cloning...".format(MesosConfig.deb_packaging_repository()))
        result = Utils.cmd("cd {} && git clone {} . && git fetch origin && git checkout {}".format(
                                                            path,
                                                            MesosConfig.deb_packaging_repository(),
                                                            MesosConfig.deb_packaging_sha() ))
        if result['ExitCode'] == 0:
            LOG.info("Done.")
            # TODO: apply patches for deb-packaging, if any...
            return True
        else:
            Utils.print_result_error(LOG, "Failed.", result)
            return False

def validate_input():
    mesos_version = MesosConfig.mesos_version()
    operating_system = MesosConfig.operating_system()
    if mesos_version == "":
        Utils.exit_with_cmd_error( __file__, "Mesos version not given. Run with show-releases to see what the available versions are.")
    if operating_system == "":
        Utils.exit_with_cmd_error( __file__, "Operating system not given. Available values: {}".format( str(MesosConfig.supported_operating_systems()) ))
    if not mesos_version in list_releases():
        Utils.exit_with_cmd_error( __file__,
                                   "Mesos version ({}) is not supported. Run with show-releases to see what the available versions are.".format(
                                    mesos_version ))
    if not operating_system in MesosConfig.supported_operating_systems():
        Utils.exit_with_cmd_error( __file__,
                                   "Operating system ({}) is not supported. Available values: {}".format(
                                    operating_system,
                                    str(MesosConfig.supported_operating_systems()) ))
    if operating_system == "osx" and Utils.platform() != "darwin":
        Utils.exit_with_cmd_error( __file__, "Operating system (osx) is only supported when running this program on OS X." )

def list_releases():
    result = Utils.cmd("cd {} && git tag -l".format(MesosConfig.mesos_repository_dir()))
    if result['ExitCode'] == 0:
        releases = result['StdOut'].split("\n")
        releases.append(MesosConfig.mesos_master_branch())
        return releases
    else:
        Utils.print_result_error(LOG, "Failed listing releases.", result)
        return []

def validate_osx_dependencies():
    # TODO: implement
    return True

def build_with_docker(build_dir_mesos, build_dir_packaging, packages_dir):
    image_name = "mesos-docker-build-{}".format(MesosConfig.operating_system().replace(":","-"))
    # Do we have the Docker image?
    LOG.info("Checking for Docker image...")
    result = Utils.cmd("docker images") # Simply make sure we have docker operational
    if result['ExitCode'] != 0:
        Utils.print_result_error(LOG, "Not able to list Docker images. Is Docker installed and running?", result)
        exit(105)
    # repeat, grep returns 1 if text not found
    result = Utils.cmd("docker images | grep {}".format(image_name))
    if result['StdOut'] == "":
        LOG.info("Docker image not found. Building...")
        result = Utils.cmd( "cd {}/{} && docker build --no-cache --force-rm=true -t {} .".format(
                            MesosConfig.docker_templates_dir(),
                            MesosConfig.operating_system().replace(":", "\\:"),
                            image_name ) )
        if result['ExitCode'] != 0:
            Utils.print_result_error(LOG, "Docker image creation failed. Is Docker installed and running?", result)
            exit(106)
    mesos_build_command = "docker run -ti -v {}:/mesos-deb-packaging -v {}:/mesos-src {} /bin/bash -c 'cd /mesos-deb-packaging && ./build_mesos --build-version {} --src-dir /mesos-src; exit $?'".format(
                                  build_dir_packaging,
                                  build_dir_mesos,
                                  image_name,
                                  MesosConfig.mesos_build_version() )
    Utils.cmd("echo '{}'".format(mesos_build_command))
    LOG.info("Building Mesos {} for {}. This will take a while...".format(MesosConfig.mesos_version(), MesosConfig.operating_system()))
    build_start_time = int(time.time())
    build_status = Utils.cmd(mesos_build_command)
    build_end_time = int(time.time())
    if build_status['ExitCode'] == 0:
        Utils.cmd("mkdir -p {0} && rm -Rf {0}/*".format( packages_dir ))
        Utils.cmd("mv {}/*.deb {}/ 2>/dev/null".format( build_dir_packaging, packages_dir ))
        Utils.cmd("mv {}/*.rpm {}/ 2>/dev/null".format( build_dir_packaging, packages_dir ))
        Utils.cmd("mv {}/*.egg {}/ 2>/dev/null".format( build_dir_packaging, packages_dir ))#
        LOG.info( "Mesos {} for {} built successfully. Build took {} seconds. Output available in {}. Cleaning up...".format(
                    MesosConfig.mesos_version(),
                    MesosConfig.operating_system(),
                    str( build_end_time - build_start_time ),
                    packages_dir ))
        Utils.cmd("rm -rf {}".format(build_dir_mesos))
        Utils.cmd("rm -rf {}".format(build_dir_packaging))
    else:
        LOG.error( "Mesos build failed. Leaving build log and temp directories for inspection. mesos={}; packaging={}".format( build_dir_mesos, build_dir_packaging ) )
        exit(107)

def build_with_osx(build_dir_mesos, build_dir_packaging, packages_dir):
    # TODO: provide correct implementation
    Utils.cmd( "cd {} && ./build_mesos --build-version {} --src-dir {}".format(
                    Config.deb_packaging_repository_dir(),
                    Config.args().mesos_build_version,
                    Config.mesos_repository_dir() ) )

## ----------------------------------------------------------------------------------------------
## OPERATIONS:
## ----------------------------------------------------------------------------------------------

def op_show_releases():
    if ensure_sources():
        LOG.info("Releases:")
        for line in list_releases():
            if line != "":
                print line

def op_show_builds():
    path = MesosConfig.packages_dir()
    for name in [ name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) ]:
        print name

def op_remove_build():
    validate_input()
    if not Utils.confirm("You are about to remove Mesos build for {} {}.".format(
            MesosConfig.mesos_version(),
            MesosConfig.operating_system() )):
        exit(0)
    Utils.cmd("rm -rf {}/{}-{}".format( MesosConfig.packages_dir(),
                                        MesosConfig.mesos_version(),
                                        MesosConfig.operating_system().replace(":", "-")))

def op_show_mesos_sources():
    show_sources('mesos')

def op_show_packaging_sources():
    show_sources('mesos-packaging')

def show_sources(kind):
    path = "{}/{}/".format(MesosConfig.source_dir(), kind)
    for name in os.listdir(path):
        full_path  = os.path.join(path, name)
        git_config = "{}/.git/config".format(full_path)
        if os.path.isfile(git_config):
            file = open(git_config, 'r')
            data = Utils.parse_git_config( file.readlines() )
            file.close()
            if 'remote "origin"' in data:
                if 'url' in data['remote "origin"']:
                    print "{} in directory {}".format(
                        data['remote "origin"']['url'],
                        full_path )

def op_remove_mesos_sources():
    if not Utils.confirm("You are about to remove Mesos sources ({}).".format(MesosConfig.source_dir())):
        exit(0)
    Utils.cmd("rm -rf {}".format(MesosConfig.source_dir()))

def op_remove_packaging_sources():
    # TODO: implement
    return False

def op_check_this_system():
    # TODO: implement
    # Check for Docker
    # Check if all build dependencies are available (OSX only)
    return False

def op_docker_image():
    # TODO: implement
    return False

def op_build():

    if ensure_sources() and ensure_deb_packaging():
        validate_input()

        # create temp work dir:
        build_dir_mesos    = "{}/{}-{}".format( MesosConfig.work_dir(),
                                        MesosConfig.mesos_version(),
                                        MesosConfig.operating_system().replace(":", "-") )
        build_dir_packaging = "{}/{}-{}-packaging".format( MesosConfig.work_dir(),
                                        MesosConfig.mesos_version(),
                                        MesosConfig.operating_system().replace(":", "-") )
        packages_dir        = "{}/{}-{}".format( MesosConfig.packages_dir(),
                                        MesosConfig.mesos_version(),
                                        MesosConfig.operating_system().replace(":", "-") )

        ## LOOKUP order:
        #   - <sha>-<mesos-version>-<os-family>-<os-version>
        #   - <sha>-<mesos-version>-<os-family>
        #   - <sha>-<os-family>-<os-version>
        #   - <sha>-<os-family>
        #   - <sha>
        patch_files = [
            "{}/{}-{}-{}.patch".format(
                                MesosConfig.packages_patches_dir(),
                                MesosConfig.deb_packaging_sha(),
                                MesosConfig.mesos_version(),
                                MesosConfig.operating_system().replace(":", "-") ),
            "{}/{}-{}-{}.patch".format(
                                MesosConfig.packages_patches_dir(),
                                MesosConfig.deb_packaging_sha(),
                                MesosConfig.mesos_version(),
                                MesosConfig.operating_system().split(":")[0] ),
            "{}/{}-{}.patch".format(
                                MesosConfig.packages_patches_dir(),
                                MesosConfig.deb_packaging_sha(),
                                MesosConfig.operating_system().replace(":", "-") ),
            "{}/{}-{}.patch".format(
                                MesosConfig.packages_patches_dir(),
                                MesosConfig.deb_packaging_sha(),
                                MesosConfig.operating_system().split(":")[0] ),
            "{}/{}.patch".format(
                                MesosConfig.packages_patches_dir(),
                                MesosConfig.deb_packaging_sha() ) ]

        build_log_file = "{}.{}.log".format(build_dir_mesos, str(int(time.time())))
        LOG.info("Recording build process to {}.".format(build_log_file))
        Config.set_cmd_log(build_log_file)

        if os.path.exists(packages_dir):
            if not Utils.confirm("Mesos build for {} {} already exists. To rebuild, continue.".format(
                    MesosConfig.mesos_version(),
                    MesosConfig.operating_system() )):
                exit(0)

        # cleanup old data:
        Utils.cmd("rm -rf {}".format(packages_dir))
        Utils.cmd("rm -rf {}".format(build_dir_mesos))
        Utils.cmd("rm -rf {}".format(build_dir_packaging))

        # copy sources
        LOG.info("Fetching Mesos {} sources...".format(MesosConfig.mesos_git_repository()))
        Utils.cmd("cp -R {} {}".format( MesosConfig.mesos_repository_dir(), build_dir_mesos ))
        Utils.cmd("cp -R {} {}".format( MesosConfig.deb_packaging_repository_dir(), build_dir_packaging ))

        patch_file_to_use = None
        for patch_file in patch_files:
            if os.path.isfile(patch_file):
                patch_file_to_use = patch_file
                break

        if patch_file_to_use != None:
            LOG.info("Found a patch file {} for mesos-deb-packaging. Applying...".format( patch_file_to_use ))
            result = Utils.cmd("cd {} && git apply {}".format(build_dir_packaging, patch_file_to_use))
            if result['ExitCode'] != 0:
                Utils.print_result_error(LOG, "Patch could not be applied to {}.".format( build_dir_packaging ), result)
                exit(105)
            else:
                LOG.info("Patch applied.")
        else:
            LOG.info("No patches for mesos-deb-packaging {}.".format( MesosConfig.deb_packaging_sha() ))

        # ensure branch / tag
        LOG.info("Ensuring Mesos version {}...".format(MesosConfig.mesos_version()))
        result = Utils.cmd("sleep 5 && cd {} && git checkout {}".format(build_dir_mesos, MesosConfig.mesos_version()))
        if result['ExitCode'] == 0:
            if MesosConfig.mesos_version() == MesosConfig.mesos_master_branch():
                LOG.info("Updating source code for {}...".format(MesosConfig.mesos_version()))
                result = Utils.cmd("cd {} && git pull origin {}".format(build_dir_mesos, MesosConfig.mesos_version()))
                if result['ExitCode'] != 0:
                    Utils.print_result_error(LOG, "Mesos version {} could not be updated from {}.".format(
                                                    MesosConfig.mesos_version(),
                                                    MesosConfig.mesos_git_repository() ), result)
                    exit(104)
                else:
                    LOG.info("Done.")

            # We have the right sources now:
            if MesosConfig.operating_system() == "osx":
                build_with_osx( build_dir_mesos, build_dir_packaging, packages_dir )
            else:
                build_with_docker( build_dir_mesos, build_dir_packaging, packages_dir )

        else:
            Utils.print_result_error(LOG, "Mesos version {} could not be checked out from {}.".format(
                                            MesosConfig.mesos_version(),
                                            MesosConfig.mesos_git_repository() ), result)
            exit(103)

if __name__ == "__main__":

    if "build" == MesosConfig.command(): op_build()
    if "docker" == MesosConfig.command(): op_docker_image()
    if "show-releases" == MesosConfig.command(): op_show_releases()
    if "show-builds" == MesosConfig.command(): op_show_builds()
    if "remove-build" == MesosConfig.command(): op_remove_build()
    if "show-mesos-sources" == MesosConfig.command(): op_show_mesos_sources()
    if "show-packaging-sources" == MesosConfig.command(): op_show_packaging_sources()
    if "remove-mesos-sources" == MesosConfig.command(): op_remove_mesos_sources()
    if "remove-packaging-sources" == MesosConfig.command(): op_remove_packaging_sources()
    if "check-this-system" == MesosConfig.command(): op_check_this_system()
    