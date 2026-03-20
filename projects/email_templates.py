def build_project_update_email_html(
    project_title,
    update_title,
    update_description,
    total_donated,
    target_amount,
    funding_percentage,
    remaining_amount,
    exceeded_amount,
    is_goal_reached,
):
    status_text = "Funding goal reached" if is_goal_reached else "Funding in progress"

    extra_line = (
        f"<p style='margin:0;color:#16a34a;font-size:14px;'><strong>Exceeded amount:</strong> {exceeded_amount}</p>"
        if exceeded_amount and exceeded_amount > 0
        else f"<p style='margin:0;color:#334155;font-size:14px;'><strong>Remaining amount:</strong> {remaining_amount}</p>"
    )

    return f"""
    <div style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;">
      <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
        <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;">
          <div style="background:#0f172a;padding:24px 28px;">
            <h1 style="margin:0;color:#ffffff;font-size:24px;">Project Progress Update</h1>
            <p style="margin:8px 0 0;color:#cbd5e1;font-size:14px;">Transparent Charity Notifications</p>
          </div>

          <div style="padding:28px;">
            <p style="margin:0 0 12px;color:#475569;font-size:14px;">Project</p>
            <h2 style="margin:0 0 20px;color:#0f172a;font-size:26px;">{project_title}</h2>

            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:18px;margin-bottom:24px;">
              <p style="margin:0 0 8px;color:#475569;font-size:14px;">Latest update</p>
              <h3 style="margin:0 0 10px;color:#111827;font-size:20px;">{update_title}</h3>
              <p style="margin:0;color:#334155;font-size:15px;line-height:1.7;">{update_description}</p>
            </div>

            <div style="margin-bottom:24px;">
              <h3 style="margin:0 0 14px;color:#111827;font-size:18px;">Funding Progress</h3>

              <div style="background:#e5e7eb;border-radius:999px;height:12px;overflow:hidden;margin-bottom:12px;">
                <div style="background:#2563eb;width:{min(float(funding_percentage), 100):.2f}%;height:12px;"></div>
              </div>

              <p style="margin:0 0 14px;color:#0f172a;font-size:16px;">
                <strong>{funding_percentage}% funded</strong>
              </p>

              <div style="display:grid;grid-template-columns:1fr;gap:10px;">
                <p style="margin:0;color:#334155;font-size:14px;"><strong>Total donated:</strong> {total_donated}</p>
                <p style="margin:0;color:#334155;font-size:14px;"><strong>Target amount:</strong> {target_amount}</p>
                <p style="margin:0;color:#334155;font-size:14px;"><strong>Status:</strong> {status_text}</p>
                {extra_line}
              </div>
            </div>

            <div style="padding-top:18px;border-top:1px solid #e5e7eb;">
              <p style="margin:0;color:#64748b;font-size:13px;line-height:1.6;">
                You are receiving this email because you donated to this project or subscribed to its updates.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
    """