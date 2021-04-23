# IRI Mapping Validator
### _for Australian Government Linked Data Working Group-issued IRIs_

This repository contains a simple set of scripts for validating the mappings of persistent IRIs allocated by the [Australian Government Linked Data Working Group (AGLDWG)](https://www.linked.data.gov.au).

The script - a Python script - operates by sending Internet requests for each AGLDWG managed persistent IRI and comparing the responses with the static comparison data stored in this repository.

## Use
Typical use is like this:

```bash
python validator.py linked.data.gov.au-vocabs.json,linked.data.gov.au-ontologies.json
```
Here the validator is run with two input files - for linked.data.gov.au vocabs & ontologies.

## Test Format
Redirection tests use JSON files for to/from IRI in this format:

```json
{
  "https://linked.data.gov.au/dataset/geofabric": [
    {
      "label": "Geofabric - distributed as Linked Data, HTML",
      "from_iri": "https://linked.data.gov.au/dataset/geofabric",
      "from_headers": null,
      "to_iri": "https://geofabricld.net",
      "to_headers": null
    },
    {
      "label": "Geofabric - distributed as Linked Data, Accept Turtle",
      "from_iri": "https://linked.data.gov.au/dataset/geofabric",
      "from_headers": {
        "Accept": "text/turtle"
      },
      "to_iri": "https://geofabricld.net/index.ttl",
      "to_headers": {
        "Content-Type": "text/turtle"
      }
    }
  ]
}
```
Each allocated IRI - in the above case `https://linked.data.gov.au/dataset/geofabric` - can have any number of individual tests. Here there is a test for HTML & RDF (Turtle) redirects.

See the JSON files in this directory for all tests implemented so far.


## License
This repository is licensed under Creative Commons 4.0 International. See the [LICENSE deed](LICENSE) in this repository for details.


## Contacts
System Owner:  [Australian Government Linked Data Working Group](http://linked.data.gov.au)

System Owner contact:  
**Nicholas Car**  
*Co-chair, AGLDWG*  
Research School of Computer Science  
Australian National University   
<nicholas.car@anu.edu.au>
