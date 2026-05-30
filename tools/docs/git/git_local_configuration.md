---
title: Git Local Configuration
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: Local environment setup for Git and SSH authentication, specifically for Fedora Linux.
tags:
  - git
  - development
---
---
options:
  type: guide
  version: 1.0.0
  birth: '2026-05-03'
  token_size: 519
---
# Git Local Configuration

This document describes the local environment setup for Git and SSH authentication within this project, specifically for Fedora Linux.

## SSH Key Authentication (GitHub)

To avoid entering the SSH passphrase for every Git operation, we utilize the system-provided `ssh-agent` combined with the `AddKeysToAgent` configuration.

### Key Details
- **Identity File:** `/home/commi/.ssh/id_github`
- **Agent Socket:** `/run/user/1000/ssh-agent.socket` (System default on Fedora)

### Configuration Steps

Instead of using shell scripts in `.bashrc`, which can be unreliable or redundant on Fedora, use the SSH config file.

1. **Edit (or create) your SSH config file:**
   ```bash
   nano ~/.ssh/config
   ```

2. **Add the following configuration block:**
   ```ssh
   Host github.com
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_github
       AddKeysToAgent yes
   ```

### How it Works
- **`IdentityFile`**: Explicitly tells SSH which private key to use for GitHub.
- **`AddKeysToAgent yes`**: Instructs the SSH client to automatically load the key into the `ssh-agent` the first time it is used.

**Workflow:**
1. The first time you run a Git command (e.g., `git fetch`) after a reboot, you will be prompted for the passphrase.
2. Once entered, the key is stored in the system's memory.
3. All subsequent commands and all new terminal sessions will use the cached key without prompting for the passphrase until the system is rebooted.

### Troubleshooting
If you are still asked for the passphrase repeatedly:
1. Verify the agent is running: `echo $SSH_AUTH_SOCK`
2. Check if the key is loaded: `ssh-add -l`
3. Manually add the key to test: `ssh-add /home/commi/.ssh/id_github`
