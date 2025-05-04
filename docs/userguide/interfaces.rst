Supported Interfaces
====================

Setuptools is a complicated library with many interface surfaces and challenges. In addition to its primary purpose as a packaging build backend, Setuptools also has historically served as a standalone builder, installer, uploader, metadata provider, and more. Additionally, because it's implemented as a Python library, its entire functionality is incidentally exposed as a library.

In addition to operating as a library, because newer versions of Setuptools are often used to build older (sometimes decades-old) packages, it has a high burden of stability.

In order to have the ability to make sensible changes to the project, downstream developers and consumers should avoid depending on internal implementation details of the library and should rely only on the supported interfaces:

- *Documented APIs* are expected to be extremely stable and have deprecation notices and periods prior to backward incompatible changes or removals.
- *Functional and Integration tests* that capture specific behaviors and expectations about how the library and system is intended to work for outside users.
- *Code comments and docstrings* (including in tests) may provide specific protections to limit the changes to behaviors on which a downstream consumer can rely.

Depending on other behaviors is risky and subject to future breakage. If a project wishes to consider using interfaces that aren't covered above, consider requesting those interfaces to be added prior to depending on them (perhaps through a pull request implementing the change).
