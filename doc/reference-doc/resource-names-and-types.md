# Resource names and types

## Mapping Names of Resource to Short Names

The following table provides an overview of resource names
(e.g. "lastModifiedTime") and their mappings to short resource names
(e.g. "lt") as used in a given JSON.

| Resource short name | Resource long name    |
|:-------------------:|:---------------------:|
| aei                 | AE-ID                 |
| ch                  | childResource         |
| csi                 | CSE-ID                |
| cst                 | CSE type              |
| ct                  | creationTime          |
| et                  | expirationTime        |
| fu   			      | filterUsage           |
| lt   			   	  | lastModifiedTime      |
| poa  			   	  | pointOfAccess         |
| ri   			   	  | resourceID            |
| rn   			   	  | resourceName          |
| rr   			   	  | **TODO**              |
| rsc  			   	  | ResponseStatusCode    |
| srt  			   	  | supportedResourceType |
| ty   			   	  | resourceType          |

## Numerical Representations of Resource Types

The table below specifies the numerical representations of a given
resource types (selection).

| Num | Resource type     |
|:---:|:-----------------:|
| 2   | AE                |
| 3   | container         |
| 4   | contentInstance   |
| 5   | CSEBase           |
| 16  | remoteCSE         |
| 23  | subscription      |


All available resource types are implemented in the enumeration class
`ResourceTypeE`, defined in
[model.py](../../common/openmtc-onem2m/src/openmtc_onem2m/model.py).
