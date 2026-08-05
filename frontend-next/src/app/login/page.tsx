"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import { Wrench } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ApiError, login } from "@/lib/api";

/**
 * Portão de autenticação mínimo para alcançar as duas telas do protótipo
 * (Dashboard e Ordens de Serviço). Não é uma das telas avaliadas pela Sprint
 * NEXTJS-FUNDAÇÃO — é a infraestrutura necessária para chegar nelas usando a
 * sessão real do Flask via proxy de dev (ver frontend-next/README.md).
 */
export default function LoginPage() {
  const router = useRouter();
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(usuario, senha);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Falha ao autenticar.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-svh flex-1 items-center justify-center bg-muted/30 p-6">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="w-full max-w-sm"
      >
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="items-center gap-2 text-center">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Wrench weight="bold" className="size-5" />
            </div>
            <CardTitle className="text-xl font-semibold tracking-tight">
              Fluxoly
            </CardTitle>
            <CardDescription>
              Protótipo Next.js — entre com um usuário do sistema real.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="usuario" className="text-sm font-medium text-foreground">
                  Usuário
                </label>
                <Input
                  id="usuario"
                  name="usuario"
                  autoComplete="username"
                  autoFocus
                  value={usuario}
                  onChange={(e) => setUsuario(e.target.value)}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="senha" className="text-sm font-medium text-foreground">
                  Senha
                </label>
                <Input
                  id="senha"
                  name="senha"
                  type="password"
                  autoComplete="current-password"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  required
                />
              </div>
              {error && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm text-destructive"
                  role="alert"
                >
                  {error}
                </motion.p>
              )}
              <Button type="submit" disabled={loading} className="mt-1 w-full">
                {loading ? "Entrando..." : "Entrar"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
