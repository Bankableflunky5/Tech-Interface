JOB_REPORT_TEMPLATE = """
<div style="width: 100%; font-family: 'Segoe UI', sans-serif; font-size: 12pt; margin: 0; padding: 0;">
    <!-- Title Section -->
    <div style="text-align: center;">
        <h1 style="color: #000; font-size: 28pt; margin: 0;">Job Report</h1>
        <h2 style="font-size: 16pt; font-weight: normal; color: transparent; margin: 30px 0;">ㅤ</h2> <!-- spacer -->
    </div>

    <!-- Centered Table Container -->
    <div style="width: 700px; margin: 0 auto;">
        <!-- Customer Info Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <colgroup>
                <col style="width: 40%;">
                <col style="width: 60%;">
            </colgroup>
            <thead>
                <tr>
                    <th style="padding: 8px; border: 1px solid #000; background: #f0f0f0;">Customer Information</th>
                    <th style="padding: 8px; border: 1px solid #000; background: #f0f0f0;">Details</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>JobID:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{job_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Name:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{customer_first_name} {customer_sur_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Phone:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{customer_phone}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Email:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{customer_email}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>House Number:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{customer_door_number}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Post Code:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{customer_post_code}</td>
                </tr>
            </tbody>
        </table>

        <!-- Spacer Heading Between Tables -->
        <h2 style="font-size: 16pt; font-weight: normal; color: transparent; margin: 30px 0;">ㅤ</h2>

        <!-- Device Info Table -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 50px;">
            <colgroup>
                <col style="width: 40%;">
                <col style="width: 60%;">
            </colgroup>
            <thead>
                <tr>
                    <th style="padding: 8px; border: 1px solid #000; background: #f0f0f0;">Device Details</th>
                    <th style="padding: 8px; border: 1px solid #000; background: #f0f0f0;">Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Date:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{start_datetime}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Device Type:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{device_type}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Device Brand:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{device_brand}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Device Model:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{device_model}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Extras:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{extras}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Issue:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{issue}</td>
                </tr>
                <tr>
                   <td style="padding: 8px; border: 1px solid #000;"><strong>Password:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{password}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;"><strong>Data Save:</strong></td>
                    <td style="padding: 8px; border: 1px solid #000;">{data_save}</td>
                </tr>
            </tbody>
        </table>
    </div>
"""