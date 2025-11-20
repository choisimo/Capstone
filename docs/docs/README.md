# Documentation Directory

Organized documentation for the Capstone project.

## Directory Structure

```
docs/
├── planning/          # Active planning and requirements documents
│   ├── frontend/      # Frontend specifications and plans
│   └── backend/       # Backend PRDs and service specifications
├── architecture/      # Architecture documents and decisions
├── runbooks/          # Operational procedures and service docs
├── api/               # API contracts and specifications
└── _archive/          # Historical/deprecated documentation
    ├── legacy_prd/    # Old Product Requirements Documents
    ├── legacy_services/ # Old Service documentation
    └── ...            # Other archived content
```

## Planning Documents (planning/)

Active planning and requirements documentation:

- **Frontend**: Dashboard specifications, UI/UX plans, and integration guides.
- **Backend**: Detailed PRDs, service specifications, and system requirements.

## Architecture Documents (architecture/)

High-level architecture, system design, and integration patterns:

- Service discovery policies
- System architecture diagrams
- Integration patterns
- GCP architecture (if applicable)

## Runbooks (runbooks/)

Operational procedures and service-specific documentation:

- Service deployment guides
- Troubleshooting procedures
- Configuration references
- Maintenance procedures

## API Documentation (api/)

API contracts, specifications, and events:

- REST API specifications
- Event schemas
- Service contracts
- Integration guides

## Archived Documentation (_archive/)

Historical documentation and deprecated content:

- **legacy_prd**: Old PRD documents that are no longer active.
- **legacy_services**: Deprecated service documentation (superseded by runbooks).
- Historical project documents and reports.

## Contributing

When adding new documentation:

1. Choose the appropriate directory based on content type.
2. Use clear, descriptive filenames with kebab-case.
3. Include a date in filename for time-sensitive docs: `YYYY-MM-DD-description.md`.
4. Keep documents focused and single-purpose.
5. Move outdated docs to `_archive/` rather than deleting.