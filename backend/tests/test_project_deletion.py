import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.sql.dml import Delete

from app.api.errors import ApiError
from app.api.routes import delete_project
from app.db.models import Project
from app.schemas.common import ProjectDelete
from app.services.projects import delete_project_records


class ProjectDeleteContractTests(unittest.TestCase):
    def test_explicit_true_confirmation_is_required(self):
        self.assertEqual(ProjectDelete.model_validate({"expected_revision": 1, "confirm": True}).confirm, True)
        for payload in (
            {"expected_revision": 1},
            {"expected_revision": 1, "confirm": False},
            {"expected_revision": 1, "confirm": "yes"},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ProjectDelete.model_validate(payload)

    def test_route_cascades_children_only_after_revision_check(self):
        project_id = uuid4()
        project = Project(id=project_id, revision=3, name="Disposable fixture", purpose="")
        db = Mock()
        db.scalar.return_value = project
        body = ProjectDelete(expected_revision=3, confirm=True)

        with patch("app.api.routes.delete_project_records") as cascade, patch("app.api.routes._event"):
            response = delete_project(project_id, body, db)

        self.assertEqual(response.status_code, 204)
        cascade.assert_called_once_with(db, project_id)
        db.flush.assert_called_once()
        db.delete.assert_called_once_with(project)
        db.commit.assert_called_once()

    def test_stale_revision_does_not_cascade_or_delete(self):
        project_id = uuid4()
        db = Mock()
        db.scalar.return_value = Project(id=project_id, revision=2, name="Disposable fixture", purpose="")

        with patch("app.api.routes.delete_project_records") as cascade:
            with self.assertRaises(ApiError) as error:
                delete_project(project_id, ProjectDelete(expected_revision=1, confirm=True), db)

        self.assertEqual(error.exception.code, "stale_revision")
        cascade.assert_not_called()
        db.delete.assert_not_called()

    def test_cascade_statements_are_project_scoped_and_fk_ordered(self):
        project_id = uuid4()
        db = Mock()

        delete_project_records(db, project_id)

        statements = [call.args[0] for call in db.execute.call_args_list]
        self.assertTrue(all(isinstance(statement, Delete) for statement in statements))
        # Junctions and versions precede their parents, then roles/operations/activity.
        self.assertEqual(len(statements), 7)
        for statement in statements:
            self.assertIn("project_id", str(statement.whereclause))
            self.assertIn(str(project_id), str(statement.compile().params))


if __name__ == "__main__":
    unittest.main()
