import requests
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal

GITHUB = Namespace("http://github.com/")
GITHUB_REPO = Namespace("http://github.com/repo/")
GITHUB_USER = Namespace("http://github.com/user/")

class Repo:
    graph = None
    iri = None
    data = None
    owner = None
    name = None
    token = None

    def auth(self):
        return {
            "Authorization": f"Bearer {self.token}"
        }

    def save(self):        
        open(f"{self.data['name']}.nt", "w").write(
            self.graph.serialize(format="ntriples")
        )


def get_repo(owner, name, token):
    repo = Repo()
    repo.token = token

    data = requests.get(f"https://api.github.com/repos/{owner}/{name}", headers=repo.auth()).json()

    repo.data = data
    repo.graph = Graph()
    repo.iri = GITHUB_REPO[data["full_name"]]
    repo.owner = owner
    repo.name = name

    repo.graph.add((repo.iri, RDF.type, GITHUB.Repository))

    repo.graph.add((repo.iri, RDFS.label, Literal(repo.data["full_name"])))
    repo.graph.add((repo.iri, GITHUB.hasDescription, Literal(repo.data["description"])))
    repo.graph.add((repo.iri, GITHUB.isPrivate, Literal(repo.data["private"])))

    repo.graph.add((repo.iri, GITHUB.hasOwner, GITHUB_USER[repo.data["owner"]["login"]]))
    repo.graph.add((repo.iri, GITHUB.createdAt, Literal(repo.data["created_at"])))

    return repo

def model_commits(repo: Repo, branch: str):
    url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/commits"
    params = {
        "sha": branch,  # the branch you want to get the commits from
        "per_page": 100   # the number of commits per page (max 100)
    }

    response = requests.get(url, params=params, headers=repo.auth())

    if response.status_code == 200:
        commits = response.json()

        branches_iri = URIRef(f"{repo.iri}/branch/{branch}")

        for commit in commits:
            commit_iri  = URIRef(commit["html_url"])

            repo.graph.add((branches_iri, GITHUB.hasCommit, commit_iri))
            if commit["author"] is not None:
                author = GITHUB_USER[commit["author"]["login"]]
                repo.graph.add((commit_iri, GITHUB.author, author))
            
            if "message" in commit:
                repo.graph.add((commit_iri, GITHUB.message, Literal(commit["message"])))


    else:
        print("Error: ", response.status_code)

def model_contributors(repo: Repo):
    contributors_url = repo.data["contributors_url"]
    contributors_response = requests.get(contributors_url, headers=repo.auth())
    contributors_data = contributors_response.json()

    for contributor in contributors_data:
        contributor_uri = GITHUB_USER[contributor["login"]]
        repo.graph.add((repo.iri, GITHUB.hasContributor, contributor_uri))
        repo.graph.add((contributor_uri, RDF.type, GITHUB.User))
        repo.graph.add((contributor_uri, RDFS.label, Literal(contributor["login"])))
        repo.graph.add((contributor_uri, GITHUB.hasAvatar, URIRef(contributor["avatar_url"])))

def model_branches(repo: Repo):
    branches_url = f"https://api.github.com/repos/{repo.owner}/{repo.name}/branches"
    branches_response = requests.get(branches_url, headers=repo.auth())
    branches_data = branches_response.json()
    for branch in branches_data:
        branches_uri = URIRef(f"{repo.iri}/branch/{branch['name']}")
        repo.graph.add((repo.iri, GITHUB.hasBranch, branches_uri))
        repo.graph.add((branches_uri, RDF.type, GITHUB.Branch))
        repo.graph.add((branches_uri, RDFS.label, Literal(branch["name"])))
        repo.graph.add((branches_uri, GITHUB.isProtected, Literal(branch['protected'])))
        
        model_commits(repo, branch["name"])

def hovud(owner, name, token):
    repo = get_repo(owner, name, token)
    model_contributors(repo)
    model_branches(repo)

    repo.save()


if __name__ == "__main__":
    import sys
    message = """
Usage:
python hovud.py <REPO_OWNER> <REPO_NAME> <TOKEN>

To get token:
git credential fill
protocol=https
host=github.com

Hit enter twice. Your token should appear as "password".
"""
    if sys.argv[1] in ["-h", "--help", "h", "help"]:
        print(message)
    elif len(sys.argv) < 3:
        raise Exception(message)
    else:
        eigar = sys.argv[1]
        depot = sys.argv[2]
        token = sys.argv[3]
        hovud(eigar, depot, token)
