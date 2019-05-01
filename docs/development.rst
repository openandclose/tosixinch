
Development
===========

Test
----

Tests are done on linux. Other platforms are not considered.


URL quoting memo
----------------

Spec
^^^^

``URL`` is:
    ``scheme://authority/path;parameters?query#fragment``

``Authority`` is:
    ``user:password@host:port``

``Unreserved characters`` are:
    ``ALPHA DIGIT -._~``

``Reserved characters`` are:
    * ``gen-delims:  #/:?@[]``
    * ``sub-delims:  !$&'()*+,;=``

``Excluded characters`` (not defined in RFC 3986) are:
    ``"%<>\^`{|}``

Allowed characters for each url components are
(This is a simplified version of RFC 3986 one.):

    * ``userinfo  = *( unreserved / pct-encoded / sub-delims / ":" )``
    * ``host      = *( unreserved / pct-encoded / sub-delims / "[" / "]" )``
    * ``port      = *DIGIT``
    * ``path      = *( unreserved / pct-encoded / sub-delims / ":" / "@")``
    * ``query     = *( unreserved / pct-encoded / sub-delims / ":" / "@" / "/" / "?" )``
    * ``fragment  = *( unreserved / pct-encoded / sub-delims / ":" / "@" / "/" / "?" )``

Windows illegal filename characters are:
    ``/:?*\"<>|``

    * https://msdn.microsoft.com/en-us/library/aa365247
    * https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words

Note
^^^^

* I suppose that defining
  some conversion strategy for URL references to file references
  is a common enough concern,
  since many applications (such as site downloading or mirroring)
  have to implement it.
  But I cannot find the general documents
  (or stackoverflow Q&As).

* Even ``princexml`` began escaping '?' around 2015.

    * https://www.princexml.com/forum/topic/2914/svg-filenames-with-special-characters


Rules
^^^^^

In some places in the script,
We rewrite ``src`` or ``href`` links to refer to newly downloaded local files.

The general principle is that
for local filenames, we unquote all characters in urls,
since they are easier to read.

It is 'lossy' conversion,
e.g. filename ``'aaa?bbb'`` might have been url ``'aaa?bbb'`` or ``'aaa%3Fbbb'``.

Link urls are made using original urls as much as possible.
Only delimiters for the relevant url components are newly quoted
(A very limited set of ``reserved characters``).

Note that link urls are always scheme-less and authority-less,
because they refer to local files the script creates.
Local references are made from
stripping scheme and turning authority to the first path.

So path component now might have special characters for authority.
They are ``'@:[]'``, in which ``'[]'`` are  illegal for path.
Therefore we have to quote them.

.. note::
    ``':'`` in the first path component in relative reference is illegal. But

    1. We 'normalize' relative reference starting with slashes
    2. We always add ``'./'`` for relative-path reference

    So we can ignore it.

Query delimiter is the first ``'?'``,
and query and fragment can have the second and third ``'?'``,
so we have to quote *all* occurrences of ``'?'``.

Query and fragment can also have ``'/'``,
and tend to do some special things (by servers).
For query, we change it to some other nonspecial character (``'_'``),
because otherwise, it might make too many directories.
For fragment, we keep it as it is
(The present implementation strips fragments in the first stages anyway).

According to RFC, parameters are not used, password is deprecated.
So we ignore ``';'``, but consider ``':'``, respectively.

For Windows, illegal filename characters are all changed to ``'_'``.
More semantic changing may be possible
(e.g. opening ``'<'`` to opening ``'['``),
but the selecting the right ones is rather hard.

For now, we are ignoring ASCII control characters
and non ASCII characters.


result
^^^^^^

.. code-block:: none

    _           quote       replace
    path        []
    query       ?           /
    fragment    ?
