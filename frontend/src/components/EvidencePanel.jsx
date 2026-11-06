import { useEffect, useState } from 'react'
import { errorMessage, getEvidence, getScreenshotUrl } from '../api'

function Section({ title, children }) {
    return (
        <div className="mt-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</div>
            <div className="mt-1 text-sm">{children}</div>
        </div>
    )
}
// 
const isBlockedNoise = (m) => m.text.includes('net::ERR_FAILED')

export default function EvidencePanel({ resultId }) {
    const [evidence, setEvidence] = useState(null)
    const [imageUrl, setImageUrl] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        let cancelled = false
        let url = null

        getEvidence(resultId)
            .then((data) => {
                if (cancelled) return
                setEvidence(data)
                if (data.has_screenshot) {
                    getScreenshotUrl(resultId)
                        .then((u) => {
                            if (cancelled) URL.revokeObjectURL(u)
                            else {
                                url = u
                                setImageUrl(u)
                            }
                        })
                        .catch(() => { })
                }
            })
            .catch((err) => !cancelled && setError(errorMessage(err)))

        return () => {
            cancelled = true
            if (url) URL.revokeObjectURL(url)
        }
    }, [resultId])

    if (error) return <p className="mt-3 text-sm text-red-700">{error}</p>
    if (!evidence) return <p className="mt-3 text-sm text-slate-500">Loading evidence...</p>

    // If a request succeeded, any validation messages come from the page the
    // browser landed on afterwards, so they are not relevant to this case.
    const succeeded = evidence.api_calls.some((c) => c.status >= 200 && c.status < 300)
    const realConsoleErrors = evidence.console_errors.filter((m) => !isBlockedNoise(m))
    const blockedCount = evidence.console_errors.length - realConsoleErrors.length

    return (
        <div className="mt-3 rounded-md border bg-slate-50 p-3">
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="Final page screenshot"
                    className="max-h-96 w-full rounded border bg-white object-contain object-top"
                />
            )}

            <Section title="Final URL">{evidence.final_url || '-'}</Section>

            <Section title="Network requests (non-GET)">
                {evidence.api_calls.length === 0 ? (
                    <span className="text-slate-500">None. No request was sent.</span>
                ) : (
                    <ul className="font-mono text-xs">
                        {evidence.api_calls.map((c, i) => (
                            <li key={i}>
                                {c.method} {c.status} {c.url}
                            </li>
                        ))}
                    </ul>
                )}
            </Section>

            {evidence.validation_messages.length > 0 && !succeeded && (
                <Section title="Browser validation messages">
                    <ul className="list-disc pl-5">
                        {evidence.validation_messages.map((v, i) => (
                            <li key={i}>
                                {v.field}: {v.message}
                            </li>
                        ))}
                    </ul>
                </Section>
            )}

            {evidence.http_errors.length > 0 && (
                <Section title="HTTP errors during this case">
                    <ul className="font-mono text-xs">
                        {evidence.http_errors.map((e, i) => (
                            <li key={i}>
                                {e.method} {e.status} {e.url}
                            </li>
                        ))}
                    </ul>
                </Section>
            )}

            {(realConsoleErrors.length > 0 || blockedCount > 0) && (
                <Section title="Console errors">
                    {realConsoleErrors.length > 0 && (
                        <ul className="font-mono text-xs">
                            {realConsoleErrors.map((m, i) => (
                                <li key={i}>{m.text}</li>
                            ))}
                        </ul>
                    )}
                    {blockedCount > 0 && (
                        <p className="mt-1 text-xs text-slate-500">
                            {blockedCount} "Failed to load resource" error(s) hidden: these are third-party
                            fonts, images and payment scripts blocked on purpose by the test browser's safety
                            rules, not application defects.
                        </p>
                    )}
                </Section>
            )}

            <Section title="Page text">
                <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded bg-white p-2 text-xs">
                    {evidence.page_text || '-'}
                </pre>
            </Section>
        </div>
    )
}