import requests
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal

# Define namespaces
GITHUB = Namespace("http://github.com/")
GITHUB_REPO = Namespace("http://github.com/repo/")
GITHUB_USER = Namespace("http://github.com/user/")

# Define the repository to retrieve data for
repo_owner = "markus-ap"
repo_name = "paprika"

# Retrieve data from the GitHub API
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
response = requests.get(url)
data = response.json()

# Create an RDF graph
g = Graph()

# Add the repository as a resource
repo_uri = GITHUB_REPO[repo_owner + "/" + repo_name]
g.add((repo_uri, RDF.type, GITHUB.Repository))

# Add metadata about the repository
g.add((repo_uri, RDFS.label, Literal(data["full_name"])))
g.add((repo_uri, GITHUB.hasDescription, Literal(data["description"])))
#g.add((repo_uri, GITHUB.hasHomepage, URIRef(data["homepage"])))

# Add contributors as resources
contributors_url = data["contributors_url"]
contributors_response = requests.get(contributors_url)
contributors_data = contributors_response.json()
for contributor in contributors_data:
    contributor_uri = GITHUB_USER[contributor["login"]]
    g.add((repo_uri, GITHUB.hasContributor, contributor_uri))
    g.add((contributor_uri, RDF.type, GITHUB.User))
    g.add((contributor_uri, RDFS.label, Literal(contributor["login"])))
    g.add((contributor_uri, GITHUB.hasAvatar, URIRef(contributor["avatar_url"])))

branches_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches"
branches_response = requests.get(branches_url)
branches_data = branches_response.json()
for branch in branches_data:
    branches_uri = URIRef(f"{repo_uri}/branch/{branch['name']}")
    g.add((repo_uri, GITHUB.hasBranch, branches_uri))
    g.add((branches_uri, RDF.type, GITHUB.Branch))
    g.add((branches_uri, RDFS.label, Literal(branch["name"])))
    g.add((branches_uri, GITHUB.isProtected, Literal(branch['protected'])))

# Print the graph
open(f"{data['name']}.trig", "w").write(
    g.serialize(format="trig")
)