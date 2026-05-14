# 🚀 Getting Started with Lorenzetti

The Lorenzetti framework is best utilized through pre-built container images for ease of use and dependency management.

## 📦 Container Images

The easiest way to use Lorenzetti is by employing either **Docker** or **Singularity** based on the official images provided at the [Lorenzetti's DockerHub](https://hub.docker.com/r/lorenzetti/lorenzetti).

For technical details on how these container images are generated, please refer to the [Lorenzetti GitHub repository's docker branch](https://github.com/lorenzetti-ufrj-br/lorenzetti/tree/master/docker).


## Running as a Container

### Singularity (Recommended)

Singularity is the recommended engine for running the Lorenzetti framework.

Pull the image:

```bash
singularity pull docker://lorenzetti/lorenzetti:latest
```

Run the container:

```bash
singularity run lorenzetti_latest.sif
```


## 🛠️ Manual Installation (Inside the Container)

Once you have entered the running container (using `singularity run` or `docker run`), follow these steps to download and install the simulator.


**Clone the repository and enter the directory:**

```bash
git clone https://github.com/lorenzetti-ufrj-br/lorenzetti.git && cd lorenzetti
```

**Build the framework:**

```bash
make
```

**Setup the environment:**

This command will set up all necessary environment variables to run the Lorenzetti framework.

```bash
source build/lzt_setup.sh
```




## 🖥️ GUI Application Setup (Optional - Linux Only with Docker)

Run the container with X11 forwarding (for GUI):
```bash
docker run -e DISPLAY=$DISPLAY -v ${HOME}:${HOME} -v /tmp/.X11-unix:/tmp/.X11-unix -v $XAUTHORITY:/tmp/.XAuthority -e XAUTHORITY=/tmp/.XAuthority  -it lorenzetti/lorenzetti:latest
```

This step is only necessary if you need to run graphical user interface (GUI) applications *inside* the container and forward them to your Linux host machine.

**Install Xorg on the host machine:**
```bash
sudo apt-get install xorg
```

**Disable host access control:**

This command allows the container to forward the GUI interface to the host machine.

```bash
xhost +
```
> **Note:** For security, remember to revoke access after your session by running `xhost -`.

> **Note:** To run the event display, use the command `run_vis.py`

