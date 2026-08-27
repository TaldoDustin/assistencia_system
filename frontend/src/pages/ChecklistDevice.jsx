import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  CircleNotch,
  Microphone,
  QrCode,
  DeviceMobile,
  SpeakerHigh,
  Camera,
  CheckCircle,
} from "@phosphor-icons/react";
import { toast } from "sonner";
import { checklist as checklistApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, PanelContent } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/ui/error-state";
import { Reveal } from "@/components/ui/reveal";
import { getOrderDisplayNumber } from "@/lib/constants";

const TOUCH_CELL_COUNT = 20;

function statusLabel(status) {
  if (status === "ok") return "OK";
  if (status === "falha") return "Falha";
  return "Não testado";
}

function statusVariant(status) {
  if (status === "ok") return "success";
  if (status === "falha") return "error";
  return "neutral";
}

function StatusButtons({ value, onChange }) {
  const options = [
    { key: "ok", label: "OK" },
    { key: "falha", label: "Falha" },
    { key: "nao_testado", label: "Não testado" },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <Button
          key={option.key}
          type="button"
          variant={value === option.key ? "default" : "outline"}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  );
}

function Section({ children }) {
  return (
    <Panel>
      <PanelContent className="p-5 space-y-4">{children}</PanelContent>
    </Panel>
  );
}

export default function ChecklistDevice() {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [ordem, setOrdem] = useState(null);
  const [existingChecklist, setExistingChecklist] = useState(null);
  const [executadoPor, setExecutadoPor] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [touchMap, setTouchMap] = useState(() => Array.from({ length: TOUCH_CELL_COUNT }, () => false));
  const [draggingTouch, setDraggingTouch] = useState(false);
  const [testStatus, setTestStatus] = useState({
    touch: "nao_testado",
    audio: "nao_testado",
    microfone: "nao_testado",
    camera: "nao_testado",
    botoes: "nao_testado",
  });
  const [audioPlayed, setAudioPlayed] = useState(false);
  const [micState, setMicState] = useState({ supported: true, recording: false, previewUrl: "", error: "" });
  const [cameraState, setCameraState] = useState({ supported: true, active: false, error: "" });
  const [buttonChecks, setButtonChecks] = useState({ power: false, volumeUp: false, volumeDown: false, silent: false });
  const audioContextRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const cameraStreamRef = useRef(null);
  const cameraVideoRef = useRef(null);

  useEffect(() => {
    checklistApi.getPublic(token).then((res) => {
      if (!res?.ok) {
        toast.error(res?.erro || "Nao foi possivel carregar o checklist");
        setLoading(false);
        return;
      }

      const checklist = res.checklist || {};
      const savedTests = checklist.resultado?.testes || {};
      setOrdem(res.ordem || null);
      setExistingChecklist(checklist);
      setExecutadoPor(checklist.executado_por || "");
      setObservacoes(checklist.observacoes || "");
      setTestStatus({
        touch: checklist.status_touch || "nao_testado",
        audio: checklist.status_audio || "nao_testado",
        microfone: checklist.status_microfone || "nao_testado",
        camera: checklist.status_camera || "nao_testado",
        botoes: checklist.status_botoes || "nao_testado",
      });

      if (Array.isArray(savedTests.touch?.cells) && savedTests.touch.cells.length === TOUCH_CELL_COUNT) {
        setTouchMap(savedTests.touch.cells.map(Boolean));
      }
      if (savedTests.audio?.played) {
        setAudioPlayed(true);
      }
      if (savedTests.botoes?.checks) {
        setButtonChecks({
          power: Boolean(savedTests.botoes.checks.power),
          volumeUp: Boolean(savedTests.botoes.checks.volumeUp),
          volumeDown: Boolean(savedTests.botoes.checks.volumeDown),
          silent: Boolean(savedTests.botoes.checks.silent),
        });
      }
      setLoading(false);
    }).catch(() => {
      toast.error("Nao foi possivel carregar o checklist");
      setLoading(false);
    });

    return () => {
      if (cameraStreamRef.current) {
        cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, [token]);

  useEffect(() => {
    const finishDrag = () => setDraggingTouch(false);
    window.addEventListener("pointerup", finishDrag);
    return () => window.removeEventListener("pointerup", finishDrag);
  }, []);

  const touchCoverage = useMemo(() => {
    const touched = touchMap.filter(Boolean).length;
    return Math.round((touched / TOUCH_CELL_COUNT) * 100);
  }, [touchMap]);

  const suggestedTouchStatus = useMemo(() => {
    if (touchCoverage >= 90) return "ok";
    if (touchCoverage > 0) return "falha";
    return "nao_testado";
  }, [touchCoverage]);

  const suggestedButtonsStatus = useMemo(() => {
    const values = Object.values(buttonChecks);
    if (values.every(Boolean)) return "ok";
    if (values.some(Boolean)) return "falha";
    return "nao_testado";
  }, [buttonChecks]);

  const markTouchCell = (index) => {
    setTouchMap((current) => current.map((cell, i) => (i === index ? true : cell)));
  };

  const handleTouchPointer = (event) => {
    const index = Number(event.currentTarget.dataset.cellIndex);
    if (Number.isInteger(index)) {
      markTouchCell(index);
    }
  };

  const playAudioTest = async () => {
    try {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor) {
        toast.error("Seu navegador nao suporta audio programatico");
        return;
      }

      if (!audioContextRef.current || audioContextRef.current.state === "closed") {
        audioContextRef.current = new AudioContextCtor();
      }

      const ctx = audioContextRef.current;
      await ctx.resume();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(440, ctx.currentTime);
      oscillator.frequency.linearRampToValueAtTime(660, ctx.currentTime + 0.8);
      gainNode.gain.setValueAtTime(0.001, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 1.25);
      setAudioPlayed(true);
      toast.success("Som reproduzido");
    } catch {
      toast.error("Nao foi possivel reproduzir o som");
    }
  };

  const startMicTest = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setMicState((current) => ({ ...current, supported: false, error: "Microfone nao suportado neste navegador." }));
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const previewUrl = URL.createObjectURL(blob);
        setMicState({ supported: true, recording: false, previewUrl, error: "" });
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setMicState((current) => ({ ...current, supported: true, recording: true, error: "" }));
    } catch {
      setMicState((current) => ({ ...current, recording: false, error: "Permissao negada ou microfone indisponivel." }));
    }
  };

  const stopMicTest = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const startCameraTest = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraState({ supported: false, active: false, error: "Camera nao suportada neste navegador." });
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      cameraStreamRef.current = stream;
      if (cameraVideoRef.current) {
        cameraVideoRef.current.srcObject = stream;
      }
      setCameraState({ supported: true, active: true, error: "" });
    } catch {
      setCameraState({ supported: true, active: false, error: "Nao foi possivel acessar a camera." });
    }
  };

  const stopCameraTest = () => {
    if (cameraStreamRef.current) {
      cameraStreamRef.current.getTracks().forEach((track) => track.stop());
      cameraStreamRef.current = null;
    }
    if (cameraVideoRef.current) {
      cameraVideoRef.current.srcObject = null;
    }
    setCameraState((current) => ({ ...current, active: false }));
  };

  const saveChecklist = async () => {
    setSaving(true);
    try {
      const payload = {
        executado_por: executadoPor,
        observacoes,
        origem: "qr_publico",
        testes: {
          touch: {
            status: testStatus.touch === "nao_testado" ? suggestedTouchStatus : testStatus.touch,
            cobertura_percentual: touchCoverage,
            cells: touchMap,
          },
          audio: {
            status: testStatus.audio,
            played: audioPlayed,
          },
          microfone: {
            status: testStatus.microfone,
            gravacao_disponivel: Boolean(micState.previewUrl),
          },
          camera: {
            status: testStatus.camera,
            visualizacao_ativa: cameraState.active,
          },
          botoes: {
            status: testStatus.botoes === "nao_testado" ? suggestedButtonsStatus : testStatus.botoes,
            checks: buttonChecks,
          },
        },
      };

      const res = await checklistApi.savePublic(token, payload);
      if (!res?.ok) {
        toast.error(res?.erro || "Nao foi possivel salvar o checklist");
        return;
      }
      setExistingChecklist(res.checklist || null);
      setTestStatus({
        touch: res.checklist?.status_touch || payload.testes.touch.status,
        audio: res.checklist?.status_audio || payload.testes.audio.status,
        microfone: res.checklist?.status_microfone || payload.testes.microfone.status,
        camera: res.checklist?.status_camera || payload.testes.camera.status,
        botoes: res.checklist?.status_botoes || payload.testes.botoes.status,
      });
      toast.success("Checklist salvo com sucesso");
    } catch {
      toast.error("Nao foi possivel salvar o checklist");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <CircleNotch className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!ordem) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-6">
        <div className="w-full max-w-md">
          <ErrorState
            title="Checklist indisponível"
            description="O link informado não encontrou um aparelho válido para teste."
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center justify-center gap-2">
          <img src="/brand/fluxoly-icon-inverted.svg" alt="" className="h-8 w-8 rounded-lg" />
          <span className="font-wordmark text-lg text-foreground">Fluxoly</span>
        </div>

        <Reveal className="space-y-6">
          <Section>
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-primary/15 p-3">
                <DeviceMobile className="h-6 w-6 text-primary" />
              </div>
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Checklist de entrada</p>
                <h1 className="text-2xl font-semibold text-foreground">OS #{getOrderDisplayNumber(ordem)}</h1>
                <p className="text-sm text-muted-foreground">{ordem.cliente} • {ordem.modelo || "Modelo não informado"}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl border border-border bg-muted p-3">
                <p className="text-muted-foreground">Cor</p>
                <p className="font-medium text-foreground">{ordem.cor || "Não informada"}</p>
              </div>
              <div className="rounded-xl border border-border bg-muted p-3">
                <p className="text-muted-foreground">IMEI</p>
                <p className="font-medium text-foreground">{ordem.imei || "Não informado"}</p>
              </div>
            </div>

            {existingChecklist?.atualizado_em ? (
              <div className="rounded-xl border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
                Último checklist salvo em {existingChecklist.atualizado_em}.
              </div>
            ) : null}
          </Section>

          <Section>
            <div className="flex items-center gap-3">
              <QrCode className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Identificação</h2>
            </div>
            <div className="space-y-2">
              <Label htmlFor="executado-por">Quem executou o checklist</Label>
              <Input
                id="executado-por"
                value={executadoPor}
                onChange={(event) => setExecutadoPor(event.target.value)}
                placeholder="Nome do técnico ou cliente"
              />
            </div>
          </Section>

          <Section>
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Touch</h2>
                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                  Passe o dedo por toda a grade. Cobertura atual: {touchCoverage}%
                  <Badge variant={statusVariant(suggestedTouchStatus)}>{statusLabel(suggestedTouchStatus)}</Badge>
                </div>
              </div>
              <CheckCircle className="h-5 w-5 text-primary shrink-0" />
            </div>
            <div className="grid grid-cols-4 gap-2">
              {touchMap.map((touched, index) => (
                <button
                  key={index}
                  type="button"
                  data-cell-index={index}
                  onPointerDown={(event) => {
                    setDraggingTouch(true);
                    handleTouchPointer(event);
                  }}
                  onPointerEnter={(event) => {
                    if (draggingTouch) handleTouchPointer(event);
                  }}
                  className={`aspect-square rounded-xl border transition-colors ${touched ? "bg-primary border-primary" : "bg-muted border-border"}`}
                />
              ))}
            </div>
            <StatusButtons value={testStatus.touch} onChange={(value) => setTestStatus((current) => ({ ...current, touch: value }))} />
          </Section>

          <Section>
            <div className="flex items-center gap-3">
              <SpeakerHigh className="h-5 w-5 text-primary" />
              <div>
                <h2 className="text-lg font-semibold text-foreground">Alto-falante</h2>
                <p className="text-sm text-muted-foreground">Reproduza o som e confirme se ele sai limpo.</p>
              </div>
            </div>
            <Button type="button" onClick={playAudioTest}>Reproduzir som de teste</Button>
            <p className="text-sm text-muted-foreground">Som reproduzido: {audioPlayed ? "sim" : "não"}</p>
            <StatusButtons value={testStatus.audio} onChange={(value) => setTestStatus((current) => ({ ...current, audio: value }))} />
          </Section>

          <Section>
            <div className="flex items-center gap-3">
              <Microphone className="h-5 w-5 text-primary" />
              <div>
                <h2 className="text-lg font-semibold text-foreground">Microfone</h2>
                <p className="text-sm text-muted-foreground">Grave um trecho curto e escute a reprodução.</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={startMicTest} disabled={micState.recording}>Iniciar gravação</Button>
              <Button type="button" variant="outline" onClick={stopMicTest} disabled={!micState.recording}>Parar gravação</Button>
            </div>
            {micState.error ? <p className="text-sm text-warning">{micState.error}</p> : null}
            {micState.previewUrl ? <audio controls src={micState.previewUrl} className="w-full" /> : null}
            <StatusButtons value={testStatus.microfone} onChange={(value) => setTestStatus((current) => ({ ...current, microfone: value }))} />
          </Section>

          <Section>
            <div className="flex items-center gap-3">
              <Camera className="h-5 w-5 text-primary" />
              <div>
                <h2 className="text-lg font-semibold text-foreground">Câmera</h2>
                <p className="text-sm text-muted-foreground">Abra a câmera e verifique foco, imagem e tremor.</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={startCameraTest} disabled={cameraState.active}>Abrir câmera</Button>
              <Button type="button" variant="outline" onClick={stopCameraTest} disabled={!cameraState.active}>Encerrar câmera</Button>
            </div>
            {cameraState.error ? <p className="text-sm text-warning">{cameraState.error}</p> : null}
            <div className="rounded-xl overflow-hidden border border-border bg-black">
              <video ref={cameraVideoRef} autoPlay playsInline muted className="w-full min-h-56 object-cover" />
            </div>
            <StatusButtons value={testStatus.camera} onChange={(value) => setTestStatus((current) => ({ ...current, camera: value }))} />
          </Section>

          <Section>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Botões físicos</h2>
              <p className="text-sm text-muted-foreground">Marque os botões que responderam corretamente.</p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                ["power", "Power"],
                ["volumeUp", "Volume +"],
                ["volumeDown", "Volume -"],
                ["silent", "Silent / vibração"],
              ].map(([key, label]) => (
                <label key={key} className="flex items-center gap-3 rounded-xl border border-border bg-muted px-4 py-3">
                  <Checkbox
                    checked={buttonChecks[key]}
                    onCheckedChange={(checked) => setButtonChecks((current) => ({ ...current, [key]: Boolean(checked) }))}
                  />
                  <span className="text-foreground">{label}</span>
                </label>
              ))}
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              Sugestão automática:
              <Badge variant={statusVariant(suggestedButtonsStatus)}>{statusLabel(suggestedButtonsStatus)}</Badge>
            </div>
            <StatusButtons value={testStatus.botoes} onChange={(value) => setTestStatus((current) => ({ ...current, botoes: value }))} />
          </Section>

          <Section>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Observações</h2>
              <p className="text-sm text-muted-foreground">Registre riscos, trincas, oxidação, marcas ou qualquer detalhe importante.</p>
            </div>
            <Textarea
              value={observacoes}
              onChange={(event) => setObservacoes(event.target.value)}
              placeholder="Ex.: touch falhando no canto superior direito; aparelho com marcas na tampa."
              className="min-h-32"
            />
          </Section>

          <div className="sticky bottom-4">
            <Button type="button" onClick={saveChecklist} disabled={saving} className="w-full h-12 text-base">
              {saving ? <CircleNotch className="mr-2 h-4 w-4 animate-spin" /> : null}
              Salvar checklist
            </Button>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
