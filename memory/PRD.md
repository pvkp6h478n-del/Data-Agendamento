# DockSync — PRD

## Problema original
Aplicativo para agendar manualmente entregas de transportadoras e permitir que a empresa consulte, via QR Code, o que chegará no dia ou na semana.

## Personas
- Administrador de portaria/logística: cadastra e mantém os agendamentos.
- Colaborador de recebimento e segurança: consulta chegadas sem editar dados.

## Requisitos principais
- Login exclusivo para administradores.
- Campos: transportadora, fornecedor, nota fiscal, data, horário, volumes, doca e status.
- Consulta pública com agenda do dia, próximos 7 dias e intervalo de datas.
- Filtros por transportadora e fornecedor.
- QR Code diário para abrir a consulta pública.
- Detalhes de cada chegada e CRUD administrativo.

## Arquitetura e decisões
- React com agenda responsiva e FastAPI com endpoints REST.
- MongoDB via `MONGO_URL` e `DB_NAME` existentes.
- Sessão administrativa via JWT em cookie HttpOnly.
- Dados de consulta não exigem autenticação; alterações exigem administrador.
- QR Code gerado no navegador com o endereço `/consulta?consultar=YYYY-MM-DD`.

## Implementado — 2026-10-21
- Painel consultivo com dados iniciais de exemplo, cards de resumo e tabela responsiva.
- Filtros de hoje, próximos 7 dias, intervalo, transportadora e fornecedor.
- Modal de detalhes e QR Code diário.
- Login, logout, sessão e seed de administrador.
- Criação, edição, exclusão e atualização de status dos agendamentos.
- API e fluxos integrados validados com 100% de sucesso no teste inicial.

## Backlog priorizado
- P0: múltiplos perfis administrativos e permissões por função.
- P1: exportação da agenda para Excel/PDF.
- P1: histórico de alterações e confirmação de recebimento.
- P2: notificações de chegada e impressão de manifesto.

## Próximos passos
1. Adicionar exportação para o fechamento diário da portaria.
2. Adicionar filtro por status e doca.
3. Criar histórico operacional por agendamento.
## Update 2026-06 — Exportação Excel/PDF
- Botões Excel (xlsx) e PDF (jsPDF + autotable) no painel admin e na consulta pública (/consulta)
- Exporta os filtros aplicados, com linha TOTAL de volumes e nº de agendamentos (src/lib/exportSchedule.js)
- Filtro "Hoje" agora limita a data de hoje (start=end=hoje); salvar/excluir recarrega com os filtros aplicados
- Testado: iteration_2 (100% dos fluxos)
## Backlog
- P2: Cadastro de transportadoras/fornecedores; separar App.js em componentes
