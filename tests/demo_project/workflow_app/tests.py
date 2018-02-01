from django import test

from . import models


class InternalTests(test.TestCase):
    def test_loop(self):
        author = models.Author.objects.create(name="John Doe")
        project = models.Project.objects.create(
            name="Some project",
            author=author,
        )

        project.start_developing()
        project.end_developing()
        project.reject()

        subproject = models.SubProject.objects.create(
            name="Testing session",
            project=project,
        )
        subproject.start_developing()
        subproject.end_developing()
        subproject.approve()

        self.assertEqual(models.ProjectWorkflow.states.done, subproject.state)
        self.assertEqual(models.ProjectWorkflow.states.developing, project.state)

        project.cancel()
        self.assertEqual(models.ProjectWorkflow.states.cancelled, project.state)
