"""NHTSA Shadow Recalls retrocast — code package.

The registration-pinned *documents and results* live in the sibling `retrocast/nhtsa-recalls/`
(hyphen: the slug used by PRE-REGISTRATION-v1 §9 and by the collectors). Python cannot import a
hyphenated package, so the code lives here under the underscore name. Same index, two
directories, deliberately: the frozen paths in the registration are never renamed to suit code.
"""
