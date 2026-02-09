import Link from "next/link";

export default function Nav() {
  return (
    <nav className="nav">
      <div className="nav-brand">
        <img
          className="brand-logo"
          src="/jerry-logo.png"
          alt="JERRY"
        />
        <div className="brand-text">
          <div>Retention Intelligence</div>
        </div>
      </div>
      <div className="nav-links">
        <Link href="/">Overview</Link>
        <Link href="/chat">Chat Studio</Link>
        <Link href="/dashboard">AI Eval Dashboard</Link>
      </div>
    </nav>
  );
}
