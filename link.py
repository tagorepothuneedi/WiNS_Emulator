from testh import SNR_DEFAULT,emu


def create_snr_default_matrix(ctx):
    snr_matrix=[[SNR_DEFAULT for i in range(ctx.noofnodes)] for j in range(ctx.noofnodes)]
    return snr_matrix
