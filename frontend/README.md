# Frontend Fluxoly

Aplicação React + Vite servida pelo Flask em `/app`.

## Scripts

- `npm run dev`: ambiente local com HMR
- `npm run build`: gera o bundle de produção em `frontend/dist`
- `npm run lint`: valida os arquivos `.js` e `.jsx`

## Integração

- o frontend consome a API Flask em `/api`
- no desenvolvimento, o proxy do Vite aponta para `http://localhost:5080`
- em produção, o Flask entrega `frontend/dist` nas rotas `/app` e `/app/*`
