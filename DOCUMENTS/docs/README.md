# Documentation Directory

Organized documentation for the Capstone project.

## Directory Structure

```
docs/
├── architecture/    # Architecture documents and decisions
├── runbooks/        # Operational procedures and service docs
├── adr/            # Architecture Decision Records
├── api/            # API contracts and specifications
└── archived/       # Historical/deprecated documentation
    ├── prd/        # Product Requirements Documents
    └── mkdocs/     # Old MkDocs configuration (deprecated)
```

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

## Architecture Decision Records (adr/)

Document significant architectural decisions using the ADR format:

- Why decisions were made
- Alternatives considered
- Consequences and trade-offs

## API Documentation (api/)

API contracts, specifications, and events:

- REST API specifications
- Event schemas
- Service contracts
- Integration guides

## Archived Documentation (archived/)

Historical documentation and deprecated content:

- Old PRD documents
- Deprecated MkDocs configuration
- Historical project documents
- Verification reports

## Contributing

When adding new documentation:

1. Choose the appropriate directory based on content type
2. Use clear, descriptive filenames with kebab-case
3. Include a date in filename for time-sensitive docs: `YYYY-MM-DD-description.md`
4. Keep documents focused and single-purpose
5. Move outdated docs to `archived/` rather than deleting
