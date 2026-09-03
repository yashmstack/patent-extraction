# vendor/

## opsin-core-2.9.0.jar

OPSIN, the Open Parser for Systematic IUPAC Nomenclature. A grammar that derives a
structure from a systematic chemical name. No model, no database, no network.

It was already a stage here (`resolve_names.py`), but calling the public service at
opsin.ch.cam.ac.uk, because the docstring's machine had no Java. This one does
(OpenJDK 21), so the jar is vendored and the parse runs offline, pinned to one
version, and identical on every machine. A pinned jar also means a name that parsed
last month parses the same way today, which a hosted service cannot promise.

Downloaded from https://github.com/dan2097/opsin/releases/tag/2.9.0
sha256 is in `opsin-core-2.9.0.jar.sha256`.

## OpsinBatch.java

The CLI jar writes ambiguity warnings to stderr, unaligned with the SMILES it writes
to stdout, so a batch run cannot tell which name the warning belonged to. That
matters here: an OPSIN WARNING means the name does not pin one molecule down, and
promoting that guess to a structure is the one thing this pipeline must not do.

So this wraps the library directly and emits one JSON object per line carrying the
three facts the web service returned, `status`, `smiles` and `message`, which keeps
the cache format unchanged. Java 11+ runs a single source file with no build step:

    java -cp opsin-core-2.9.0.jar OpsinBatch.java < names.txt
