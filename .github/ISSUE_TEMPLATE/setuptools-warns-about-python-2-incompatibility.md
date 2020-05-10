---
name: Setuptools warns about Python 2 incompatibility
about: Report the issue where setuptools 45 or later stops working on Python 2
title: Incompatible install in (summarize your environment)
labels: Python 2
assignees: ''

---

<!--

Please DO NOT SUBMIT this template without first investigating the issue and answering the questions below. This template is intended mainly for developers of systems and not for end users. If you are an end user experiencing the warning, please work with your system maintainers (starting with the project you're trying to use) to report the issue.

If you did not intend to use this template, but only meant to file a blank issue, just hit the back button and click "Open a blank issue".

It's by design that Setuptools 45 and later will stop working on Python 2. To ease the transition, Setuptools 45 was released to continue to have Python 2 compatibility, but emit a strenuous warning that it will stop working.

In most cases, using pip 9 or later to install Setuptools from PyPI or any index supporting the Requires-Python metadata will do the right thing and install Setuptools 44.x on Python 2.

If you've come to file an issue, it's probably because some process managed to bypass these protections.

Your first course of action should be to reason about how you managed to get an unsupported version of Setuptools on Python 2. Please complete the sections below and provide any other detail about your environment that will help us help you.

-->

## Prerequisites

<!-- These are the recommended workarounds for the issue. Please
try them first. -->

- [ ] Python 2 is required for this application.
- [ ] I maintain the software that installs Setuptools (if not, please contact that project).
- [ ] Setuptools installed with pip 9 or later.
- [ ] Pinning Setuptools to `setuptools<45` in the environment was unsuccessful.

## Environment Details

- Operating System and version:
- Python version:
- Python installed how:
- Virtualenv version (if using virtualenv): n/a

Command(s) used to install setuptools (and output):

```
```

Output of `pip --version` when installing setuptools:

```
```

## Other notes
