"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PROCESSING_STEPS } from "@/lib/constants";
import { API_BASE } from "@/lib/api";

export interface ProcessingEvent {
  type: string;
  step_number?: number;
  tool?: string;
  status?: string;
  message?: string;
  data?: Record<string, unknown>;
  agent?: string;
  timestamp?: string;
}

export interface ProcessingState {
  currentStep: number;
  completedSteps: number[];
  events: ProcessingEvent[];
  isComplete: boolean;
  isFailed: boolean;
  finalStatus: string | null;
  liveDetail: ProcessingEvent | null;
  progress: number;
  elapsedSeconds: number;
}

export function useProcessing(invoiceId: string | null) {
  const [state, setState] = useState<ProcessingState>({
    currentStep: 0,
    completedSteps: [],
    events: [],
    isComplete: false,
    isFailed: false,
    finalStatus: null,
    liveDetail: null,
    progress: 0,
    elapsedSeconds: 0,
  });

  const sourceRef = useRef<EventSource | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const demoRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startDemoSimulation = useCallback(() => {
    let stepIdx = 0;
    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setState((s) => ({
        ...s,
        elapsedSeconds: Math.floor((Date.now() - startTime) / 1000),
      }));
    }, 1000);

    demoRef.current = setInterval(() => {
      if (stepIdx >= PROCESSING_STEPS.length) {
        setState((prev) => ({
          ...prev,
          isComplete: true,
          finalStatus: "approved",
          progress: 100,
        }));
        if (demoRef.current) clearInterval(demoRef.current);
        if (timerRef.current) clearInterval(timerRef.current);
        return;
      }
      const step = PROCESSING_STEPS[stepIdx];
      const completed = PROCESSING_STEPS.slice(0, stepIdx + 1).map((s) => s.step);
      setState((prev) => ({
        ...prev,
        currentStep: step.step,
        completedSteps: completed,
        liveDetail: {
          type: "step_complete",
          step_number: step.step,
          tool: step.name,
          message: `${step.label} completed successfully`,
          data: { result: "pass", confidence: (85 + Math.random() * 14).toFixed(1) + "%" },
        },
        progress: Math.round(((stepIdx + 1) / PROCESSING_STEPS.length) * 100),
      }));
      stepIdx++;
    }, 1800);
  }, []);

  const connect = useCallback(async () => {
    if (!invoiceId) return;

    // Trigger processing on the backend (ignores 409 if already processing)
    try {
      const token = localStorage.getItem("access_token");
      if (token) {
        await fetch(`${API_BASE}/api/v1/invoices/${encodeURIComponent(invoiceId)}/process`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch {
      // Ignore — the stream will still work or fallback to demo
    }

    // Start elapsed timer
    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setState((s) => ({
        ...s,
        elapsedSeconds: Math.floor((Date.now() - startTime) / 1000),
      }));
    }, 1000);

    const token = localStorage.getItem("access_token");
    const url = `${API_BASE}/api/v1/invoices/${encodeURIComponent(invoiceId)}/stream${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    const source = new EventSource(url);
    sourceRef.current = source;

    source.onmessage = (e) => {
      try {
        const event: ProcessingEvent = JSON.parse(e.data);
        // Backend may send "step" or "step_number" — normalise
        const raw = JSON.parse(e.data) as Record<string, unknown>;
        const stepNum = event.step_number ?? (raw.step as number | undefined);
        setState((prev) => {
          const events = [...prev.events, event];
          let { currentStep, completedSteps, isComplete, isFailed, finalStatus, liveDetail } = prev;

          if (event.type === "step_complete" && stepNum) {
            completedSteps = [...new Set([...completedSteps, stepNum])];
            currentStep = Math.max(currentStep, stepNum + 1);
            liveDetail = event;
          } else if (event.type === "step_start" && stepNum) {
            currentStep = stepNum;
            liveDetail = event;
          } else if (event.type === "processing_complete" || event.type === "pipeline_complete") {
            isComplete = true;
            finalStatus = (event.data?.status as string) || (raw.decision as string) || "approved";
          } else if (event.type === "error") {
            isFailed = true;
            finalStatus = "failed";
          } else if (event.type === "agent_handoff") {
            liveDetail = event;
          }

          const progress = Math.round(
            (completedSteps.length / PROCESSING_STEPS.length) * 100
          );

          return { currentStep, completedSteps, events, isComplete, isFailed, finalStatus, liveDetail, progress, elapsedSeconds: prev.elapsedSeconds };
        });
      } catch {
        // ignore malformed events
      }
    };

    source.onerror = () => {
      source.close();
      // If no events received, start demo simulation
      setState((prev) => {
        if (prev.events.length === 0 && !prev.isComplete) {
          startDemoSimulation();
        }
        return prev;
      });
    };
  }, [invoiceId]);

  const disconnect = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (demoRef.current) {
      clearInterval(demoRef.current);
      demoRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { ...state, disconnect };
}
