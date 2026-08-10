# Vendored OKF reference-agent reader

source_ref: https://github.com/GoogleCloudPlatform/knowledge-catalog
source_commit: 930b65fc3f5619d5d0591f88c72ebae8b848d60d
license_ref: LICENSE
notice_ref: NOTICE.md

The three files under `bundle/` are copied from the source commit without
semantic edits. The smoke reads `document.py` and `paths.py`; `index.py` is
kept in the fixed vendor hash and read boundary but is not imported because
its upstream generator has an optional synthesizer dependency outside this
minimal reader surface. This repository uses the vendored source only in the
zero-network acceptance smoke.
