#!/bin/bash
git fetch --unshallow || true
hugo --gc --minify --enableGitInfo