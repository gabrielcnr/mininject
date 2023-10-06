# mininject
Minimalistic / lightweight dependency injection library for Python

It does not require importing modules ahead of time for wiring the injected dependencies.

That can be done lazily / on-demand. The dependency resolution is given by simple lookups on containers with `Injectable` dependencies. 
