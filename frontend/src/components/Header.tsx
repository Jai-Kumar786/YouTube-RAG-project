import HealthBadge from "./HealthBadge";

export default function Header() {
    return (
        <header className="header">
            <div className="header-brand">
                <h1 className="header-title">YouTube RAG</h1>
                <span className="header-subtitle">
                    Ask anything about any YouTube video
                </span>
            </div>
            <HealthBadge />
        </header>
    );
}
