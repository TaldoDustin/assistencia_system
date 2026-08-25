import { useState } from "react";
import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { auth } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelContent } from "@/components/ui/panel";

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setUser } = useAuth();
  const [form, setForm] = useState({ usuario: "", senha: "" });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const error = searchParams.get("erro");
    if (error) {
      toast.error(error);
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await auth.login(form.usuario, form.senha);
      if (data?.ok) {
        setUser(data.usuario);
        navigate("/", { replace: true });
      } else {
        toast.error(data?.erro || "Usuário ou senha inválidos");
      }
    } catch {
      toast.error("Erro ao conectar ao servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-3">
          <img
            src="/brand/fluxoly-icon-inverted.svg"
            alt=""
            className="h-12 w-12 rounded-xl mx-auto"
          />
          <div>
            <h1 className="font-wordmark text-2xl text-foreground">Fluxoly</h1>
            <p className="text-muted-foreground text-sm mt-1">Sistema de Assistência Técnica</p>
          </div>
        </div>

        <Panel>
          <PanelContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="usuario">Usuário</Label>
                <Input
                  id="usuario"
                  placeholder="seu.usuario"
                  value={form.usuario}
                  onChange={(e) => setForm((p) => ({ ...p, usuario: e.target.value }))}
                  autoComplete="username"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="senha">Senha</Label>
                <Input
                  id="senha"
                  type="password"
                  placeholder="••••••••"
                  value={form.senha}
                  onChange={(e) => setForm((p) => ({ ...p, senha: e.target.value }))}
                  autoComplete="current-password"
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Entrar
              </Button>
            </form>
          </PanelContent>
        </Panel>
      </div>
    </div>
  );
}
