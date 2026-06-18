export interface Constraints {
  category?: string;
  topology?: string;
  input_voltage_nominal_v?: number;
  output_voltage_v?: number;
  output_current_a?: number;
  temperature_min_c?: number;
  temperature_max_c?: number;
  grade?: string;
  application?: string;
  raw_input: string;
}

export interface PartIR {
  part_number: string;
  manufacturer?: string;
  category?: string;
  topology?: string;
  is_domestic: boolean;
  description?: string;
  input_voltage_min_v?: number;
  input_voltage_max_v?: number;
  output_voltage_v?: number;
  output_current_max_a?: number;
  temperature_min_c?: number;
  temperature_max_c?: number;
  package?: string;
  automotive_grade: boolean;
  lifecycle_status?: string;
  stock?: number;
  unit_price_cny?: number;
  source: string;
}

export interface ScoreBreakdown {
  parameter_match_score: number;
  supply_risk_score: number;
  cost_score: number;
  domestic_score: number;
  total_score: number;
  scoring_mode: string;
  reasons: string[];
  llm_application_score?: number;
  llm_design_risk_score?: number;
}

export interface ScoredPart {
  part: PartIR;
  score: ScoreBreakdown;
  rank?: number;
  recommendation_level?: string;
}

export interface RiskItem {
  risk_type: string;
  severity: string;
  description: string;
  related_part_number?: string;
  mitigation?: string;
}

export interface RiskIR {
  overall_risk_level: string;
  risk_items: RiskItem[];
  supply_risk_summary?: string;
  engineering_risk_summary?: string;
}

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  report?: AnalysisReport;
  isStreaming?: boolean;
  thinking?: string;          // 思考过程文本（streaming 时逐步累积）
  thinkingDone?: boolean;     // 思考过程是否已完成（主内容开始输出时置 true）
}

export interface EvidenceItem {
  part_number: string;
  claim: string;
  evidence_type: string;
  source_field: string;
  confidence: number;
  need_human_review: boolean;
}

export interface AnalysisReport {
  request_id: string;
  constraints: Constraints;
  candidates: ScoredPart[];
  recommended_parts: ScoredPart[];
  risks: RiskIR;
  evidence_count: number;
  avg_confidence: number;
  evidence_items: EvidenceItem[];
  elapsed_s: number;
  summary: string;
}

export interface Session {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}
