"""Interface local de chat com Flet (sem envio a canais externos)."""
import flet as ft
from dotenv import load_dotenv

from emporio.data import configured_path, project_root, source_from_env
from emporio.engine import Agent
from emporio.retrieval import PolicyIndex


def main(page: ft.Page):
    load_dotenv(project_root() / ".env")
    page.title = "Empório da Música | Atendimento"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 900
    page.window_height = 720
    page.scroll = ft.ScrollMode.AUTO
    try:
        agent = Agent(source_from_env(), PolicyIndex(configured_path("POLICY_PDF", "data/politicas_da_loja.pdf")))
    except Exception as exc:
        page.add(ft.Text(f"Falha ao carregar dados locais: {exc}", color=ft.Colors.RED))
        return

    history = ft.ListView(expand=True, spacing=12, auto_scroll=True)
    question = ft.TextField(label="Sua mensagem", hint_text="Ex.: Tem violão Yamaha?", expand=True)
    email = ft.TextField(label="E-mail cadastrado (somente para consultar pedidos)", width=360)
    selected_product_id: str | None = None  # Apenas referência do item, não histórico de mensagens.

    def submit(_):
        nonlocal selected_product_id
        msg = (question.value or "").strip()
        if not msg:
            return
        history.controls.append(ft.Text(f"Você: {msg}", selectable=True, weight=ft.FontWeight.BOLD))
        question.value = ""
        try:
            reply = agent.ask(
                msg, email=(email.value or "").strip() or None,
                selected_product_id=selected_product_id,
            )
            if reply.product_id:
                selected_product_id = reply.product_id
            history.controls.append(ft.Text(f"Empório: {reply.message}", selectable=True))
            if reply.sources:
                history.controls.append(ft.Text("Fontes: " + "; ".join(reply.sources), size=11, color=ft.Colors.BLUE_GREY))
            if reply.handoff:
                history.controls.append(ft.Text("Necessário atendimento humano — nenhum chamado foi aberto automaticamente.", size=12, color=ft.Colors.DEEP_ORANGE))
        except Exception:
            history.controls.append(ft.Text("Ocorreu um erro na consulta. Tente novamente ou contate a loja.", color=ft.Colors.RED))
        page.update()

    def reload_catalog(_):
        try:
            if hasattr(agent.source, "refresh_catalog"):
                agent.source.refresh_catalog()
                history.controls.append(ft.Text("Catálogo atualizado a partir dos CSVs.", color=ft.Colors.GREEN))
            else:
                history.controls.append(ft.Text("A fonte atual consulta os dados diretamente.", color=ft.Colors.BLUE_GREY))
        except (OSError, ValueError, KeyError):
            history.controls.append(ft.Text("Não foi possível atualizar o catálogo. Os dados anteriores foram mantidos.", color=ft.Colors.RED))
        page.update()

    question.on_submit = submit
    page.add(
        ft.Text("Empório da Música", size=29, weight=ft.FontWeight.BOLD),
        ft.Text("Assistente demonstrativo • preços e disponibilidade consultados nos arquivos locais"),
        ft.Container(content=history, border=ft.Border.all(1, ft.Colors.BLUE_GREY_100), border_radius=12, padding=12, expand=True),
        email,
        ft.Row([question, ft.ElevatedButton("Enviar", on_click=submit)]),
        ft.TextButton("Atualizar catálogo", on_click=reload_catalog),
        ft.Text("Atenção: não realiza compras, reservas, alterações de pedidos nem abertura de chamados.", size=12),
    )


def run():
    ft.run(main)


if __name__ == "__main__":
    run()
