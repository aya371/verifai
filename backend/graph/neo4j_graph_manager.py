"""
Neo4j Graph Manager — Identity Knowledge Graph
===============================================
Stores and queries identity relationships as a property graph.

Graph model:
  (Person)-[:WORKED_AT    {role, start, end, source}]->(Company)
  (Person)-[:STUDIED_AT   {degree, year, source}    ]->(University)
  (Person)-[:ATTENDED     {year, type}              ]->(Event)
  (Person)-[:HAS_PROFILE  {url, platform, score}    ]->(Platform)
  (Person)-[:MENTIONED_IN {snippet, url, date}       ]->(Article)

Use cases:
  - Cross-platform identity linking
  - Conflict detection (same person, different roles on different platforms)
  - Relationship queries for identity graph visualisation

NOT used for:
  - Bayesian scoring (handled by signal_normalizer + decision_fusion)
  - Simple candidate lists (handled by identity_resolver)

Save to: backend/graph/neo4j_graph_manager.py
"""
from typing import Dict, List, Optional
from backend.utils.logger import logger

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j driver not installed — graph features disabled")


class Neo4jGraphManager:
    """
    Manages the identity knowledge graph in Neo4j.
    Degrades gracefully when Neo4j is unavailable.
    """

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.driver   = None
        self.enabled  = False
        if not NEO4J_AVAILABLE:
            logger.info("Neo4j not available — running in no-graph mode")
            return
        try:
            from config import config
            _uri  = uri      or getattr(config, "NEO4J_URI", "bolt://localhost:7687")
            _user = user     or getattr(config, "NEO4J_USER", "neo4j")
            _pass = password or getattr(config, "NEO4J_PASSWORD", "")
            if not _pass:
                logger.info("Neo4j password not configured — running in no-graph mode")
                return
            self.driver = GraphDatabase.driver(_uri, auth=(_user, _pass))
            self.driver.verify_connectivity()
            self._init_constraints()
            self.enabled = True
            logger.info("Neo4j connected — graph features enabled")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e} — running in no-graph mode")

    def _init_constraints(self):
        """Create uniqueness constraints for core node types."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person)    REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company)   REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:University) REQUIRE u.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (pl:Platform) REQUIRE pl.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for cql in constraints:
                try:
                    session.run(cql)
                except Exception:
                    pass  # Constraint may already exist

    # ══════════════════════════════════════════════════════════════════════
    # WRITE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════

    def store_identity(self, name: str, osint_result: Dict, cv_result: Dict = None) -> bool:
        """
        Persist a full identity analysis into the graph.
        Creates Person node + all relationship types from OSINT and CV data.
        """
        if not self.enabled:
            return False
        try:
            with self.driver.session() as session:
                # Create Person node
                session.run(
                    "MERGE (p:Person {name: $name}) "
                    "SET p.last_updated = datetime(), "
                    "    p.osint_status = $status, "
                    "    p.identity_confidence = $conf",
                    name=name,
                    status=osint_result.get("status",""),
                    conf=osint_result.get("candidates",[{}])[0].get("similarity_score",0) if osint_result.get("candidates") else 0,
                )

                # Platform profiles
                for cand in osint_result.get("candidates", []):
                    for url in cand.get("sources", []):
                        platform = cand.get("platform","Unknown")
                        session.run(
                            "MERGE (pl:Platform {name: $platform}) "
                            "WITH pl "
                            "MATCH (p:Person {name: $name}) "
                            "MERGE (p)-[r:HAS_PROFILE {url: $url}]->(pl) "
                            "SET r.score = $score, r.extracted_info = $info",
                            platform=platform,
                            name=name,
                            url=url,
                            score=cand.get("similarity_score",0),
                            info=cand.get("extracted_info","")[:200],
                        )

                # Real-world presence (articles/mentions)
                presence = osint_result.get("real_world_presence", {})
                for signal in presence.get("signals", []):
                    if signal.get("found") and signal.get("url"):
                        session.run(
                            "MERGE (a:Article {url: $url}) "
                            "SET a.title = $title, a.type = $type "
                            "WITH a "
                            "MATCH (p:Person {name: $name}) "
                            "MERGE (p)-[r:MENTIONED_IN]->(a) "
                            "SET r.type = $type",
                            url=signal["url"],
                            title=signal.get("title","")[:200],
                            type=signal.get("type",""),
                            name=name,
                        )

                # CV-derived relationships
                if cv_result:
                    for claim in cv_result.get("claims", []):
                        self._store_cv_claim(session, name, claim)

            return True
        except Exception as e:
            logger.error(f"Neo4j store_identity failed: {e}")
            return False

    def _store_cv_claim(self, session, name: str, claim: Dict):
        """Store a single CV claim as a graph relationship."""
        claim_text = claim.get("claim", "")
        claim_type = claim.get("type", "")

        if claim_type == "employment":
            # Heuristic: extract org from claim text
            org = self._extract_org_from_claim(claim_text)
            if org:
                session.run(
                    "MERGE (c:Company {name: $org}) "
                    "WITH c "
                    "MATCH (p:Person {name: $name}) "
                    "MERGE (p)-[r:WORKED_AT]->(c) "
                    "SET r.claim = $claim, r.confidence = $conf",
                    org=org, name=name, claim=claim_text[:200],
                    conf=claim.get("confidence",""),
                )
        elif claim_type == "education":
            org = self._extract_org_from_claim(claim_text)
            if org:
                session.run(
                    "MERGE (u:University {name: $org}) "
                    "WITH u "
                    "MATCH (p:Person {name: $name}) "
                    "MERGE (p)-[r:STUDIED_AT]->(u) "
                    "SET r.claim = $claim, r.confidence = $conf",
                    org=org, name=name, claim=claim_text[:200],
                    conf=claim.get("confidence",""),
                )

    def _extract_org_from_claim(self, text: str) -> Optional[str]:
        """Heuristic extraction of organisation name from claim text."""
        import re
        # Pattern: "at [Org]" or "@ [Org]"
        m = re.search(r'\bat\s+([A-Z][A-Za-z\s&]+?)(?:\s+as|\s+from|\s+since|,|\.|\(|$)', text)
        if m:
            return m.group(1).strip()[:80]
        # "University/College/Institute" pattern
        m2 = re.search(r'([A-Z][A-Za-z\s]+(?:University|College|Institute|School|Corp|Inc|Ltd|Labs?|Technologies?))', text)
        if m2:
            return m2.group(1).strip()[:80]
        return None

    # ══════════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ══════════════════════════════════════════════════════════════════════

    def get_identity_graph(self, name: str) -> Dict:
        """
        Return the complete identity graph for a person
        as a serialisable dict for frontend visualisation.
        """
        if not self.enabled:
            return {"nodes": [], "edges": [], "available": False}
        try:
            with self.driver.session() as session:
                # Get all relationships
                result = session.run(
                    """
                    MATCH (p:Person {name: $name})-[r]->(n)
                    RETURN type(r) AS rel_type,
                           labels(n)[0] AS node_type,
                           n.name AS node_name,
                           properties(r) AS rel_props
                    """,
                    name=name
                )
                nodes = [{"id": name, "label": name, "type": "Person"}]
                edges = []
                seen_nodes = {name}

                for record in result:
                    node_name = record["node_name"] or record["rel_props"].get("url","Unknown")
                    node_type = record["node_type"]
                    if node_name not in seen_nodes:
                        nodes.append({"id": node_name, "label": node_name[:40], "type": node_type})
                        seen_nodes.add(node_name)
                    edges.append({
                        "from":  name,
                        "to":    node_name,
                        "label": record["rel_type"],
                        "props": dict(record["rel_props"]),
                    })

                return {"nodes": nodes, "edges": edges, "available": True}
        except Exception as e:
            logger.error(f"Neo4j get_identity_graph failed: {e}")
            return {"nodes": [], "edges": [], "available": False, "error": str(e)}

    def detect_conflicts(self, name: str) -> List[Dict]:
        """
        Find cases where the same person has different roles/orgs
        reported on different platforms — cross-platform conflict detection.
        """
        if not self.enabled:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Person {name: $name})-[r1:WORKED_AT]->(c1:Company),
                          (p)-[r2:WORKED_AT]->(c2:Company)
                    WHERE c1.name <> c2.name
                      AND r1.confidence = 'high'
                      AND r2.confidence = 'high'
                    RETURN c1.name AS org1, c2.name AS org2,
                           r1.claim AS claim1, r2.claim AS claim2
                    LIMIT 10
                    """,
                    name=name
                )
                conflicts = []
                for rec in result:
                    conflicts.append({
                        "type":   "Employment Conflict",
                        "org1":   rec["org1"],
                        "org2":   rec["org2"],
                        "claim1": rec["claim1"],
                        "claim2": rec["claim2"],
                        "note":   f"'{name}' linked to both '{rec['org1']}' and '{rec['org2']}' with high confidence.",
                    })
                return conflicts
        except Exception as e:
            logger.error(f"Neo4j detect_conflicts failed: {e}")
            return []

    def get_cross_platform_summary(self, name: str) -> Dict:
        """
        Returns a summary of how many platforms this person appears on
        and whether their information is consistent across them.
        """
        if not self.enabled:
            return {"platforms": [], "count": 0, "available": False}
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Person {name: $name})-[r:HAS_PROFILE]->(pl:Platform)
                    RETURN pl.name AS platform, r.url AS url, r.score AS score
                    ORDER BY r.score DESC
                    """,
                    name=name
                )
                platforms = [{"platform": rec["platform"], "url": rec["url"], "score": rec["score"]} for rec in result]
                return {"platforms": platforms, "count": len(platforms), "available": True}
        except Exception as e:
            logger.error(f"Neo4j get_cross_platform_summary failed: {e}")
            return {"platforms": [], "count": 0, "available": False}

    def close(self):
        if self.driver:
            self.driver.close()
