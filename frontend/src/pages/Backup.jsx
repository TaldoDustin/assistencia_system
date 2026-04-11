import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Download, HardDriveDownload, Loader2, Lock, RefreshCw } from "lucide-react";
import { backup as backupApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

function formatFileSize(bytes) {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function Backup() {
  const { user } = useAuth();
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const latestBackup = backups[0];

  const isAdmin = user?.perfil === "admin";

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const res = await backupApi.list();
      if (res?.ok) {
        setBackups(res.backups || []);
      } else {
        toast.error(res?.erro || "Erro ao carregar backups");
      }
    } catch {
      toast.error("Erro ao carregar backups");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchBackups();
    } else {
      setLoading(false);
    }
  }, [isAdmin]);

  const handleCreateBackup = async () => {
    setCreating(true);
    try {
      const res = await backupApi.criar();
      if (res?.ok) {
        toast.success(res?.arquivo ? `Backup criado: ${res.arquivo}` : "Backup criado com sucesso");
        fetchBackups();
      } else {
        toast.error(res?.erro || "Erro ao criar backup");
      }
    } catch {
      toast.error("Erro ao criar backup");
    } finally {
      setCreating(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente administradores podem acessar backups.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Backups</h1>
          <p className="text-muted-foreground text-sm">
            {backups.length > 0
              ? `${backups.length} backups disponiveis${latestBackup?.data ? ` • ultimo em ${latestBackup.data}` : ""}`
              : "Crie e baixe copias do banco de dados."}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchBackups} disabled={loading || creating}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button onClick={handleCreateBackup} disabled={creating}>
            {creating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <HardDriveDownload className="h-4 w-4 mr-2" />}
            {creating ? "Criando..." : "Criar backup"}
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : backups.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Nenhum backup encontrado.
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Arquivo", "Data", "Tamanho", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {backups.map((item) => (
                  <tr key={item.nome} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-card-foreground">{item.nome}</td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{item.data || "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{formatFileSize(item.tamanho)}</td>
                    <td className="px-4 py-3 text-right">
                      <a href={backupApi.download(item.nome)}>
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4 mr-2" />
                          Baixar
                        </Button>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
