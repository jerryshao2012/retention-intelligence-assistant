import Link from "next/link";
import Nav from "../components/Nav";

export default function Home() {
  return (
    <div>
      <Nav />
      <div className="container">
        <section className="hero">
          <div className="hero-card">
            <span className="badge">Multi-Agent Orchestration</span>
            <h1 className="hero-title">Retention intelligence for bankers, not just alerts.</h1>
            <p className="hero-sub">
              <b>Problem Statement</b><br/>
Bankers and Resolution Center Operators often receive attrition alerts without sufficient context. Manually researching a customer’s full history (banking relationship, recent complaints, life events) is time-consuming, leading to generic "one-size-fits-all" retention offers that fail to address the customer's specific pain points.
<br/>
<b>The Solution</b><br/>
By combining behavioral intelligence (predicting the reason for leaving) with product intelligence (finding the right solution), the system empowers bankers to move from reactive alerts to proactive, solution-oriented conversations.
            </p>
            <div className="hero-actions">
              <Link className="button" href="/chat">Launch Chat Studio</Link>
              <Link className="button secondary" href="/dashboard">View AI Eval</Link>
            </div>
          </div>
          <div className="panel">
            <h2>What the system delivers</h2>
            <div className="grid">
              <div className="card">
                <strong>Risk + Reason</strong>
                <p>Attrition scoring paired with churn drivers and segment context.</p>
              </div>
              <div className="card">
                <strong>Product Intelligence</strong>
                <p>RAG agent maps risk drivers to relevant products clients have, such as Cash Back Mastercard offers.</p>
              </div>
              <div className="card">
                <strong>Human-in-the-loop</strong>
                <p>Bankers can approve outreach or run fully automated batches.</p>
              </div>
              <div className="card">
                <strong>High-Touch + High-Volume</strong>
                <p>Supports both relationship managers and bulk retention workflows with guardrails.</p>
              </div>
              <div className="card">
                <strong>Compliance Ready</strong>
                <p>PII redaction, approval gating, and audit trails for customer communications.</p>
              </div>
              <div className="card">
                <strong>Operational Insight</strong>
                <p>Near real-time AI eval metrics and LLM judge runs tracked in the dashboard.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
