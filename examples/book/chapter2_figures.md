# Figures and diagrams

## Images

Images are regular Markdown images, resolved relative to `book.yaml`:

![The tnw logo](images/tnw-logo.svg)

## PlantUML

A sequence diagram showing a simple request/response between a client and a service, with the service calling a database:

```plantuml
@startuml
actor Client
participant Service
database DB
Client -> Service : request(id)
Service -> DB : query(id)
DB --> Service : row
Service --> Client : response(data)
@enduml
```

## Mermaid

A flowchart rendered with the Mermaid CLI [@mmdc]:

```mermaid
flowchart LR
    Start --> V{"Valid input?"}
    V -- yes --> Process --> Done
    V -- no --> Reject --> Done
```

## Imported diagrams

Diagrams can also live in their own files and be imported with a tag on its own line. A Mermaid diagram from `diagrams/flow.mmd`:

::tnw-mmd{diagrams/flow.mmd}

and a PlantUML diagram from `diagrams/schema.puml`:

::tnw-puml{diagrams/schema.puml}
