from pathlib import Path


def render_template(

    template_path,

    output_path,

    context
):

    template_path = Path(
        template_path
    )

    output_path = Path(
        output_path
    )

    template = (
        template_path
        .read_text(
            encoding="utf-8"
        )
    )

    for key, value in context.items():

        if value is None:

            print(
                "[TemplateRenderer] "
                f"'{key}' is None"
            )

        template = template.replace(

            f"{{{{{key}}}}}",

            str(value or "")
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(

        template,

        encoding="utf-8"
    )

    print(
        "[TemplateRenderer] "
        f"Rendered: "
        f"{output_path}"
    )