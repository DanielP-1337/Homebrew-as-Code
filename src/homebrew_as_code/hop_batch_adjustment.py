"""Offline hop alpha adjustment; reference recipe remains unchanged. No IBU model."""
import argparse
import math
from pathlib import Path
import yaml
from .myspeidel_put_roundtrip import private_file, write_new, digest


def positive(value, label, maximum=None):
    if type(value) not in (int,float) or not math.isfinite(value) or value <= 0:
        raise ValueError(label + ' must be a finite positive number')
    if maximum is not None and value > maximum:
        raise ValueError(label + ' exceeds maximum')
    return value


def adjust(amount_g, reference_alpha_percent, batch_alpha_percent):
    amount=positive(amount_g,'reference amount')
    reference=positive(reference_alpha_percent,'reference alpha',100)
    batch=positive(batch_alpha_percent,'batch alpha',100)
    return amount * reference / batch


def batch_plan(document, addition_id, batch_alpha_percent):
    if document.get('format')!='homebrew-as-code/confirmed-recipe-draft-v1':
        raise ValueError('Expected confirmed recipe draft')
    matches=[x for x in document['boil']['additions'] if x.get('id')==addition_id]
    if len(matches)!=1:
        raise ValueError('Expected one addition with the selected ID')
    row=matches[0]
    amount=adjust(row['reference_amount_g'],row['reference_alpha_percent'],batch_alpha_percent)
    return {'format':'homebrew-as-code/hop-batch-adjustment-v1','offline':True,
            'upload_ready':False,'source_sha256':digest(document),
            'recipe_id':document['recipe']['id'],'recipe_version':document['recipe']['version'],
            'addition_id':addition_id,'ingredient':row['ingredient'],
            'reference_amount_g':row['reference_amount_g'],
            'reference_alpha_percent':row['reference_alpha_percent'],
            'batch_alpha_percent':batch_alpha_percent,'batch_amount_g':amount,
            'remaining_min':row['remaining_min'],
            'scope':'Preserve nominal alpha-acid mass for this addition only; not an IBU calculation or full brew plan.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recipe',default='recipes/weizen-nikolaus/confirmed-draft.yaml')
    p.add_argument('--addition',default='perle-late')
    p.add_argument('--batch-alpha',required=True,type=float)
    p.add_argument('--output',required=True)
    args=p.parse_args(argv)
    try:
        target=private_file(args.output)
        document=yaml.safe_load(Path(args.recipe).read_text(encoding='utf-8-sig'))
        result=batch_plan(document,args.addition,args.batch_alpha)
        write_new(target,result)
        print(f"{result['ingredient']}: {result['batch_amount_g']:.3f} g at {result['batch_alpha_percent']:g}% alpha; {result['remaining_min']} min remaining")
        print('Local batch adjustment:',target,'; no API requests.')
        return 0
    except (ValueError,KeyError,TypeError,OSError,yaml.YAMLError) as exc:
        print('Adjustment stopped:',type(exc).__name__)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
