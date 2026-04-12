"""
SpaceAI FC - Image Encoder
============================
Convert matplotlib figures to base64 PNG strings for API responses.
"""

import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def fig_to_base64(fig) -> str:
    """
    Convert a matplotlib figure to a base64-encoded PNG string.

    Closes the figure after encoding to free memory.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return img_base64
