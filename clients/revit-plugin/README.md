# Revit Plugin Boundary

The Revit client is intentionally thin.

It should not own validation logic. It should:

- authenticate to the backend;
- fetch findings assigned to a project / model;
- focus the author on affected elements;
- push comments, approvals, and resolution state back.

## Why This Boundary Matters

If the plugin becomes the main runtime, the product collapses into a vendor-specific tool.

`AeroBIM` keeps validation and report truth in the backend. The Revit add-in is only one delivery and remediation surface.

## First Plugin Milestones

1. sign-in and project binding
2. issue list pull
3. element focus / isolate
4. status and comment pushback
5. BCF-linked roundtrip where applicable
