---
title: Filter update: unquoted colon breaks yaml
	tags:	[filter,	chart]
status: draft
status: published
version: 1.0
version: 2.0
author:
  - name: unclosed quote "value
---
# Malformed frontmatter source
The filter field still supports status=active even when the frontmatter is broken.
FAQ: Does a malformed YAML header drop the body?
Error E_FRONTMATTER_02 is raised by upstream tooling but the body must survive.
Parameter retries: integer, default 3.
See https://design.example/frontmatter for the repair guide.
