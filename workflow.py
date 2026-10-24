"""
The FoundersLens pipeline as ONE DNotifier Workflow with two named agents:

    intake --> evaluator-agent --> research-agent --> combined result

`observability=True` means every run appears in the DNotifier dashboard
(app.dnotifier.com -> Workflows) with step-by-step input/output.
"""
from dnotifier import Workflow

from agents.evaluator_agent import evaluator_agent
from agents.research_agent import research_agent


async def pipeline_entry(ctx):
    intake = dict(ctx.input or {})
    # The web app tags each run with a private job id so it can show live progress.
    ctx.state["job_id"] = intake.pop("_job_id", None)
    ctx.state["intake"] = intake

    evaluation = await ctx.run_agent("evaluator-agent", input_data=intake)
    research = await ctx.run_agent(
        "research-agent", input_data={"intake": intake, "evaluation": evaluation}
    )
    return {"intake": intake, "evaluation": evaluation, "research": research}


founderslens_workflow = Workflow(
    name="founderslens-intake-pipeline",
    description="Scores 20 evaluation criteria (Pakistan + global), then researches 20 areas.",
    observability=True,
    entry=pipeline_entry,
)
founderslens_workflow.register_agent("evaluator-agent", evaluator_agent)
founderslens_workflow.register_agent("research-agent", research_agent)
