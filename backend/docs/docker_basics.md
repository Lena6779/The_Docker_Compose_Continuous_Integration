Docker packages an application and everything it needs to run into a container. A container runs the same way on any computer that has Docker installed, which solves the "it works on my machine" problem.

An image is a read-only template used to create containers. A Dockerfile is a text file with step-by-step instructions for building an image, such as choosing a base image, copying code, and installing dependencies.

Each instruction in a Dockerfile creates a layer. Docker caches layers, so copying requirements.txt and installing dependencies before copying the rest of the code makes rebuilds much faster.

Port mapping connects a port on the host computer to a port inside a container. For example, "8000:8000" lets a browser on the host reach an API running inside the container on port 8000.

The .dockerignore file lists files that should not be copied into the image, such as virtual environments, cache folders, and .env files containing secrets.
